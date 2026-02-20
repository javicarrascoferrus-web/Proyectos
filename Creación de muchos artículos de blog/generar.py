from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

import requests

# ----------------------------
# Config por defecto
# ----------------------------
MODEL = "qwen2.5:7b-instruct-q4_0"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

REQUEST_TIMEOUT = 240
RETRIES = 3
SLEEP_BETWEEN_CALLS = 0.6

MAX_CONTEXT_CHARS = 12000  # recorta el documento para no hacer prompts gigantes

# Fallback robusto por si __file__ no existe (notebooks/otros runners)
SCRIPT_DIR = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
DOCS_DIR = SCRIPT_DIR / "documentos"
DB_PATH = SCRIPT_DIR / "blog.sqlite"
CACHE_DIR = SCRIPT_DIR / ".cache_articulos"
CACHE_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("bloggen")


@dataclass(frozen=True)
class Item:
    title: str
    category: str
    h1: str
    h2: str
    h3_raw: str


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def norm_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def strip_front_matter(md: str) -> str:
    md = norm_newlines(md)
    if md.startswith("---\n") and "\n---\n" in md:
        return md.split("\n---\n", 1)[1]
    return md


def strip_numbering_h3(title: str) -> str:
    t = title.strip()
    t = re.sub(r"^(lecci[oó]n|lesson|tema|cap[ií]tulo|unidad)\s*", "", t, flags=re.I)
    t = re.sub(r"^\s*\d+(?:[\.\-]\d+){0,6}\s*[\)\.\-–—:]*\s*", "", t)
    t = re.sub(r"^\s*[–—-]\s*", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t or title.strip()


def extract_items(md_body: str, file_stem: str) -> List[Item]:
    h1, h2 = "", ""
    out: List[Item] = []

    for line in norm_newlines(md_body).splitlines():
        if m := re.match(r"^\s*#\s+(.+?)\s*$", line):
            h1, h2 = m.group(1).strip(), ""
            continue
        if m := re.match(r"^\s*##\s+(.+?)\s*$", line):
            h2 = m.group(1).strip()
            continue
        if m := re.match(r"^\s*###\s+(.+?)\s*$", line):
            raw = m.group(1).strip()
            title = strip_numbering_h3(raw)
            h1_use = h1.strip() or "Sin sección principal"
            h2_use = h2.strip() or "Sin subsección"
            cat = f"{file_stem}, {h1_use}, {h2_use}"
            out.append(Item(title=title, category=cat, h1=h1_use, h2=h2_use, h3_raw=raw))

    return out


def build_prompt(full_doc: str, category: str, article_title: str, max_chars: int) -> str:
    # Recortamos el documento para evitar prompts enormes
    doc = full_doc.strip()
    if len(doc) > max_chars:
        doc = doc[:max_chars] + "\n\n[...documento recortado por longitud...]"

    return f"""Eres un redactor técnico experto en IA aplicada a programación.
Escribe en español, con un tono claro y práctico para programadores.

CONTEXTO (documento, úsalo para alinear terminología y enfoque):
\"\"\"{doc}\"\"\"

METADATOS:
- Categoría del artículo (contexto): {category}
- Título del artículo: "{article_title}"

TAREA:
Escribe un artículo de blog en formato Markdown sobre el título indicado.
Longitud objetivo: 900 a 1400 palabras.

Estructura mínima:
1) Introducción (por qué importa)
2) Explicación principal con ejemplos (incluye 1 bloque de código corto si ayuda)
3) Errores típicos / trampas (al menos 3)
4) Checklist accionable (5-10 puntos)
5) Cierre con "Siguientes pasos" (2-4 bullets)

REGLAS:
- NO incluyas front-matter YAML.
- NO incluyas enlaces inventados.
- Devuelve SOLO el Markdown del artículo.
"""


def cache_path(source_file: str, title: str, category: str) -> Path:
    h = hashlib.sha256(f"{source_file}\n{title}\n{category}".encode("utf-8")).hexdigest()[:20]
    return CACHE_DIR / f"{h}.json"


def ollama_generate(session: requests.Session, prompt: str, model: str, url: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_ctx": 8192},
    }

    last_err: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            text = (data.get("response") or "").strip()
            if not text:
                raise RuntimeError("Respuesta vacía de Ollama (campo 'response' vacío).")
            return text
        except Exception as e:
            last_err = e
            # backoff simple
            time.sleep(attempt)

    raise RuntimeError(
        f"Fallo llamando a Ollama tras {RETRIES} intentos.\n"
        f"- URL: {url}\n"
        f"- Modelo: {model}\n"
        f"- Último error: {last_err}"
    )


def ensure_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          date TEXT NOT NULL,
          title TEXT NOT NULL,
          content TEXT NOT NULL,
          category TEXT NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date DESC);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_posts_title_category ON posts(title, category);"
    )
    conn.commit()


def existing_pairs(conn: sqlite3.Connection) -> set[Tuple[str, str]]:
    return set(conn.execute("SELECT title, category FROM posts").fetchall())


def load_cached_content(ck: Path) -> str:
    if not ck.is_file():
        return ""
    try:
        cached = json.loads(ck.read_text(encoding="utf-8", errors="replace"))
        content = (cached.get("content") or "").strip()
        return content
    except Exception:
        return ""


def save_cache(
    ck: Path,
    source_file: str,
    category: str,
    title: str,
    model: str,
    content_md: str,
    it: Item,
) -> None:
    ck.write_text(
        json.dumps(
            {
                "source_file": source_file,
                "category": category,
                "title": title,
                "generated_at": now_iso(),
                "model": model,
                "content": content_md,
                "hierarchy": {"h1": it.h1, "h2": it.h2, "h3_raw": it.h3_raw},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def run(docs_dir: Path, db_path: Path, model: str, ollama_url: str, max_context_chars: int) -> None:
    if not docs_dir.is_dir():
        raise SystemExit(f"ERROR: No existe la carpeta: {docs_dir}")

    md_files = sorted(docs_dir.glob("*.md"))
    if not md_files:
        log.info(f"No se encontraron .md en {docs_dir}")
        return

    with sqlite3.connect(db_path) as conn, requests.Session() as session:
        ensure_db(conn)
        seen = existing_pairs(conn)

        inserted = 0
        skipped = 0

        log.info(f"Encontrados {len(md_files)} archivos en {docs_dir}")
        log.info(f"DB: {db_path}")
        log.info(f"Modelo: {model}")
        log.info("-" * 70)

        for md_path in md_files:
            raw = md_path.read_text(encoding="utf-8", errors="replace").strip()
            body = strip_front_matter(raw)

            file_stem = md_path.stem.strip() or md_path.name
            items = extract_items(body, file_stem=file_stem)
            if not items:
                log.info(f"[SKIP] {md_path.name}: no hay headings ###")
                continue

            log.info(f"\n[{md_path.name}] H3 encontrados: {len(items)}")
            batch_rows: List[Tuple[str, str, str, str]] = []

            for it in items:
                key = (it.title, it.category)
                if key in seen:
                    skipped += 1
                    log.info(f"  - (skip) Ya existe: [{it.category}] {it.title}")
                    continue

                ck = cache_path(md_path.name, it.title, it.category)

                content_md = load_cached_content(ck)
                if content_md:
                    log.info(f"  - (cache→db) [{it.category}] {it.title}")
                else:
                    log.info(f"  - (gen) [{it.category}] {it.title}")
                    prompt = build_prompt(raw, it.category, it.title, max_chars=max_context_chars)
                    content_md = ollama_generate(session, prompt, model=model, url=ollama_url)
                    if len(content_md) < 200:
                        raise RuntimeError(f"Contenido demasiado corto generado para: {it.title}")

                    save_cache(
                        ck=ck,
                        source_file=md_path.name,
                        category=it.category,
                        title=it.title,
                        model=model,
                        content_md=content_md,
                        it=it,
                    )
                    time.sleep(SLEEP_BETWEEN_CALLS)

                batch_rows.append((now_iso(), it.title, content_md, it.category))
                seen.add(key)

            if batch_rows:
                before = conn.total_changes
                conn.executemany(
                    "INSERT OR IGNORE INTO posts(date, title, content, category) VALUES(?, ?, ?, ?)",
                    batch_rows,
                )
                conn.commit()
                inserted += max(0, conn.total_changes - before)

        log.info("\n" + "=" * 70)
        log.info(f"Insertados: {inserted}")
        log.info(f"Saltados (ya existían): {skipped}")
        log.info(f"Cache: {CACHE_DIR}")
        log.info("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de posts desde Markdown usando Ollama.")
    parser.add_argument("--docs", type=str, default=str(DOCS_DIR), help="Carpeta con .md")
    parser.add_argument("--db", type=str, default=str(DB_PATH), help="Ruta a SQLite")
    parser.add_argument("--model", type=str, default=MODEL, help="Modelo Ollama")
    parser.add_argument("--url", type=str, default=OLLAMA_URL, help="URL API Ollama /api/generate")
    parser.add_argument("--max-context", type=int, default=MAX_CONTEXT_CHARS, help="Máx caracteres de contexto")
    args = parser.parse_args()

    run(
        docs_dir=Path(args.docs),
        db_path=Path(args.db),
        model=args.model,
        ollama_url=args.url,
        max_context_chars=args.max_context,
    )


if __name__ == "__main__":
    main()
