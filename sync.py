#!/usr/bin/env python3
"""Monta posts.json e img/ a partir dos posts do painel do blog ENTERness.

Uso: python3 sync.py <pasta_dos_posts_json> [pasta_das_capas]

- <pasta_dos_posts_json>: arquivos .json salvos pelo ArtifactData (collection "posts").
- [pasta_das_capas]: imagens de capa baixadas do painel, com o id do asset no nome.

Só entram posts com status "publicado" e com conteúdo real.
"""
import glob, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TYPES = {".jpg": "jpg", ".jpeg": "jpg", ".png": "png", ".webp": "webp"}


def load_docs(folder):
    docs = []
    for f in sorted(glob.glob(os.path.join(folder, "**", "*.json"), recursive=True)):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        d = d.get("data", d) if isinstance(d, dict) else None
        if isinstance(d, dict):
            docs.append(d)
    return docs


def find_cover(cover_dir, asset_id):
    if not cover_dir or not asset_id:
        return None
    safe = re.sub(r"[^A-Za-z0-9]", "", asset_id)
    for f in glob.glob(os.path.join(cover_dir, "**", "*"), recursive=True):
        ext = os.path.splitext(f)[1].lower()
        if safe in os.path.basename(f) and ext in TYPES and os.path.isfile(f):
            return f, safe, TYPES[ext]
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    docs, cover_dir = load_docs(sys.argv[1]), (sys.argv[2] if len(sys.argv) > 2 else None)
    img_dir = os.path.join(ROOT, "img")
    os.makedirs(img_dir, exist_ok=True)
    posts, used = [], set()
    for d in docs:
        body = str(d.get("body") or "")
        if d.get("status") != "publicado" or "[Cole aqui" in body or len(body.strip()) < 200:
            continue
        slug = d.get("slug") or ""
        if not re.fullmatch(r"[a-z0-9-]{1,90}", slug) or not d.get("title"):
            continue
        p = {k: d.get(k, "") for k in ["slug", "title", "category", "excerpt", "author", "publishedAt", "updatedAt", "body"]}
        found = find_cover(cover_dir, d.get("coverId"))
        if found:
            src, safe, ext = found
            name = f"{safe}.{ext}"
            dst = os.path.join(img_dir, name)
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
                shutil.copyfile(src, dst)
            p["cover"] = {"file": f"img/{name}"}
            used.add(name)
        elif d.get("coverId"):
            # capa existe no painel mas não foi baixada desta vez: mantém a anterior, se houver
            safe = re.sub(r"[^A-Za-z0-9]", "", d["coverId"])
            old = [n for n in os.listdir(img_dir) if n.startswith(safe + ".")]
            if old:
                p["cover"] = {"file": f"img/{old[0]}"}
                used.add(old[0])
        posts.append(p)
    posts.sort(key=lambda p: p.get("publishedAt") or "", reverse=True)
    for n in os.listdir(img_dir):
        if n not in used and n != ".gitkeep":
            os.remove(os.path.join(img_dir, n))
    out = {"posts": posts}
    path = os.path.join(ROOT, "posts.json")
    new = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if new != old:
        open(path, "w", encoding="utf-8").write(new)
    print(f"{len(posts)} post(s) publicado(s); capas: {len(used)}; posts.json {'alterado' if new != old else 'sem mudança'}")


if __name__ == "__main__":
    main()
