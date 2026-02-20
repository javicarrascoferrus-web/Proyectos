

from __future__ import annotations

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



MODEL = "qwen2.5:7b-instruct-q4_0"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

REQUEST_TIMEOUT = 240
RETRIES = 3
SLEEP_BETWEEN_CALLS = 0.6

SCRIPT_DIR = Path(__file__).resolve().parent
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


def build_prompt(full_doc: str, category: str, article_title: str) -> str:
    return f"""Eres un redactor técnico experto en IA aplicada a programación.
Escribe en español, con un tono claro y práctico para programadores.

CONTEXTO (documento completo, úsalo para alinear terminología y enfoque):
\"\"\"{full_doc}\"\"\"

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


def ollama_generate(session: requests.Session, prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9, "num_ctx": 8192},
    }

    last_err: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            r = session.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            text = (data.get("response") or "").strip()
            if not text:
                raise RuntimeError("Respuesta vacía de Ollama.")
            return text
        except Exception as e:
            last_err = e
            time.sleep(attempt)

    raise RuntimeError(f"Fallo llamando a Ollama tras {RETRIES} intentos: {last_err}")




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


def insert_many(conn: sqlite3.Connection, rows: Iterable[Tuple[str, str, str, str]]) -> int:
    cur = conn.executemany(
        "INSERT OR IGNORE INTO posts(date, title, content, category) VALUES(?, ?, ?, ?)",
        rows,
    )
 
    return conn.total_changes  # cambios acumulados (usaremos delta fuera)




def main() -> None:
    if not DOCS_DIR.is_dir():
        raise SystemExit(f"ERROR: No existe la carpeta: {DOCS_DIR}")

    md_files = sorted(DOCS_DIR.glob("*.md"))
    if not md_files:
        log.info(f"No se encontraron .md en {DOCS_DIR}")
        return

    with sqlite3.connect(DB_PATH) as conn, requests.Session() as session:
        ensure_db(conn)
        seen = existing_pairs(conn)

        inserted = 0
        skipped = 0
        total_before = conn.total_changes

        log.info(f"Encontrados {len(md_files)} archivos en {DOCS_DIR}")
        log.info(f"DB: {DB_PATH}")
        log.info(f"Modelo: {MODEL}")
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
                content_md = ""
                if ck.is_file():
                    try:
                        cached = json.loads(ck.read_text(encoding="utf-8"))
                        content_md = (cached.get("content") or "").strip()
                    except Exception:
                        content_md = ""

                if content_md:
                    log.info(f"  - (cache→db) [{it.category}] {it.title}")
                else:
                    log.info(f"  - (gen) [{it.category}] {it.title}")
                    prompt = build_prompt(raw, it.category, it.title)
                    content_md = ollama_generate(session, prompt)
                    if len(content_md) < 200:
                        raise RuntimeError(f"Contenido demasiado corto generado para: {it.title}")

                    ck.write_text(
                        json.dumps(
                            {
                                "source_file": md_path.name,
                                "category": it.category,
                                "title": it.title,
                                "generated_at": now_iso(),
                                "model": MODEL,
                                "content": content_md,
                                "hierarchy": {"h1": it.h1, "h2": it.h2, "h3_raw": it.h3_raw},
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
                    time.sleep(SLEEP_BETWEEN_CALLS)

                batch_rows.append((now_iso(), it.title, content_md, it.category))
                seen.add(key)

            # Insert por lote (1 commit por archivo)
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


if __name__ == "__main__":
    main()
