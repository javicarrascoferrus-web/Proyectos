

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

import requests
import torch
from diffusers import StableDiffusionPipeline


XML_IN = Path("producto.xml")
XML_OUT = Path("producto.updated.xml")
OUT_DIR = Path("generated_images")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3:latest"
OLLAMA_TIMEOUT = 300

MODEL_ID = "runwayml/stable-diffusion-v1-5"
STEPS = 30
GUIDANCE = 7.5
WIDTH, HEIGHT = 1024, 576
SEED_BASE = 12345


# -------------------------
# DATA
# -------------------------
@dataclass
class ImgNode:
    el: ET.Element
    section: str
    alt: str
    src: str


# -------------------------
# UTILS
# -------------------------
_slug_rx = re.compile(r"[^\w\s-]", flags=re.UNICODE)
_space_rx = re.compile(r"[\s_-]+")

def slug(s: str, limit: int = 80) -> str:
    s = (s or "").strip().lower()
    s = _space_rx.sub("-", _slug_rx.sub("", s)).strip("-")
    return (s or "image")[:limit]

def safe_name(section: str, alt: str, ext: str = ".png") -> str:
    return f"{slug(section)}-{slug(alt)}{ext}"

def read_text(root: ET.Element, path: str) -> str:
    el = root.find(path)
    return (el.text or "").strip() if el is not None and el.text else ""

def extract_json(text: str) -> dict:
    # Recorta al primer {...} para sobrevivir a texto extra del modelo
    i, j = text.find("{"), text.rfind("}")
    candidate = text[i:j+1] if i != -1 and j != -1 and j > i else text
    return json.loads(candidate)

def ollama_json(system: str, user: str, temp: float = 0.4) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "system": system,
        "prompt": user,
        "stream": False,
        "options": {"temperature": temp},
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
    r.raise_for_status()
    txt = (r.json().get("response") or "").strip()
    try:
        return extract_json(txt)
    except Exception:
        # Segundo intento más estricto
        payload["options"]["temperature"] = 0.2
        payload["prompt"] = user + "\n\nReturn ONLY valid JSON. No extra text."
        r2 = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        r2.raise_for_status()
        txt2 = (r2.json().get("response") or "").strip()
        return extract_json(txt2)


# -------------------------
# XML -> CONTEXT + IMAGES
# -------------------------
SECTION_PATHS = {
    "hero": "./hero",
    "problem": "./problem",
    "solution": "./solution",
    "features": "./keyFeatures",
    "audience": "./targetAudience",
    "usecases": "./useCases",
    "benefits": "./benefits",
    "integrations": "./integrations",
    "trust": "./trust",
    "cta": "./finalCTA",
    "faq": "./faq",
}

def build_context(root: ET.Element) -> dict:
    problems = [(x.text or "").strip() for x in root.findall("./problem/items/item") if (x.text or "").strip()]
    benefits = [(x.text or "").strip() for x in root.findall("./benefits/items/item") if (x.text or "").strip()]

    feats = []
    for f in root.findall("./keyFeatures/feature"):
        name = (f.findtext("name") or "").strip()
        ben = (f.findtext("benefit") or "").strip()
        if name or ben:
            feats.append({"name": name, "benefit": ben})

    return {
        "slug": read_text(root, "./meta/slug"),
        "title": read_text(root, "./meta/title"),
        "category": read_text(root, "./meta/category"),
        "valueProposition": read_text(root, "./hero/valueProposition"),
        "subtitle": read_text(root, "./hero/subtitle"),
        "problems": problems[:8],
        "benefits": benefits[:8],
        "features": feats[:10],
        "style": {
            "look": "clean, modern, premium SaaS, minimal, apple-like",
            "avoid": "text, letters, logos, watermarks, readable UI text",
            "colors": "neutral, soft gradients, subtle lighting",
        },
    }

def detect_section(root: ET.Element, src: str) -> str:
    # Busca si existe una imagen con ese src dentro de cada sección
    for section, base in SECTION_PATHS.items():
        if root.find(f"{base}//image[@src='{src}']") is not None:
            return section
    return "section"

def gather_images(root: ET.Element) -> list[ImgNode]:
    out: list[ImgNode] = []
    for el in root.findall(".//image"):
        src = (el.get("src") or "").strip()
        alt = (el.get("alt") or "").strip() or "image"
        out.append(ImgNode(el=el, section=detect_section(root, src), alt=alt, src=src))
    return out


# -------------------------
# PROMPTS
# -------------------------
def get_prompts(context: dict, imgs: list[ImgNode]) -> list[dict]:
    system = (
        "You write Stable Diffusion prompts for SaaS/edtech marketing visuals. "
        "Return ONLY valid JSON. No prose. "
        "No text/logos/watermarks. Consistent premium minimal style."
    )

    req = [{"id": i+1, "section": im.section, "alt": im.alt, "src": im.src} for i, im in enumerate(imgs)]

    user = (
        "Product context (JSON):\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        "Create English prompts for each image request. Return JSON:\n"
        '{ "images": [ {"id": 1, "prompt": "...", "negative_prompt": "..."}, ... ] }\n\n'
        "Image requests:\n"
        f"{json.dumps(req, ensure_ascii=False, indent=2)}\n\n"
        "Rules:\n"
        "- One distinct visual metaphor per section.\n"
        "- Strong negative_prompt against text/logos.\n"
        "- Keep a consistent premium minimal look.\n"
    )

    data = ollama_json(system, user)
    items = {x.get("id"): x for x in data.get("images", []) if isinstance(x, dict)}

    prompts = []
    for i in range(1, len(imgs) + 1):
        x = items.get(i, {})
        p = (x.get("prompt") or "").strip() or "premium minimal SaaS edtech concept, soft light, clean composition, ultra detailed"
        n = (x.get("negative_prompt") or "").strip() or "text, letters, words, watermark, logo, brand, blurry, low quality, artifacts"
        prompts.append({"prompt": p, "negative_prompt": n})
    return prompts


# -------------------------
# DIFFUSERS
# -------------------------
def load_sd() -> StableDiffusionPipeline:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        safety_checker=None,  # opcional: quítalo si quieres el checker por defecto
    ).to(device)

    if device == "cuda":
        try:
            pipe.enable_attention_slicing()
        except Exception:
            pass

    return pipe

def render_all(pipe: StableDiffusionPipeline, imgs: list[ImgNode], prompts: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, (im, pr) in enumerate(zip(imgs, prompts), start=1):
        fname = safe_name(im.section, im.alt)
        out_path = OUT_DIR / fname

        if not out_path.exists():
            g = torch.Generator(device=pipe.device.type).manual_seed(SEED_BASE + idx)
            res = pipe(
                prompt=pr["prompt"],
                negative_prompt=pr["negative_prompt"],
                num_inference_steps=STEPS,
                guidance_scale=GUIDANCE,
                width=WIDTH,
                height=HEIGHT,
                generator=g,
            )
            res.images[0].save(out_path)

        # Actualiza src en el XML al path relativo
        im.el.set("src", str(OUT_DIR / fname))


# -------------------------
# MAIN
# -------------------------
def main() -> None:
    if not XML_IN.exists():
        raise FileNotFoundError(f"No existe {XML_IN.resolve()}")

    tree = ET.parse(str(XML_IN))
    root = tree.getroot()

    imgs = gather_images(root)
    if not imgs:
        print("No hay nodos <image .../> en el XML. Nada que hacer.")
        return

    ctx = build_context(root)
    prompts = get_prompts(ctx, imgs)

    pipe = load_sd()
    render_all(pipe, imgs, prompts)

    tree.write(str(XML_OUT), encoding="utf-8", xml_declaration=True)
    print(f"OK -> {XML_OUT} (imágenes en {OUT_DIR}/)")

if __name__ == "__main__":
    main()
