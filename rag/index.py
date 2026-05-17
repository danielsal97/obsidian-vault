#!/usr/bin/env python3
"""
Build the vault vector index.
Run once, re-run when notes change.

Usage:
    cd <vault_root>
    pip install -r rag/requirements.txt
    python rag/index.py
"""
import re
import pickle
import sys
from pathlib import Path

VAULT = Path(__file__).parent.parent
IGNORE = {'.git', '_Archive', '.obsidian', '.claude-flow', 'rag'}
WIKI_RE = re.compile(r'\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]')
INDEX_OUT = Path(__file__).parent / 'vault_index.pkl'


def collect_chunks():
    # Pass 1: build filename → relative path map for link resolution
    name_to_path = {}
    all_files = []
    for f in VAULT.rglob('*.md'):
        if any(p in IGNORE for p in f.parts):
            continue
        all_files.append(f)
        name_to_path[f.stem] = str(f.relative_to(VAULT))

    # Pass 2: chunk each file by headings
    chunks = []
    for f in sorted(all_files):
        rel = str(f.relative_to(VAULT))
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        # Split on heading lines (keep the heading in each part)
        parts = re.split(r'\n(?=#{1,3} )', content)

        for part in parts:
            if len(part.strip()) < 50:
                continue

            heading_m = re.match(r'^(#{1,3}) (.+)', part)
            heading = heading_m.group(2).strip() if heading_m else f.stem

            # Resolve wiki-links in this section to relative paths
            raw_links = WIKI_RE.findall(part)
            links = []
            for lk in raw_links:
                lk = lk.strip()
                resolved = name_to_path.get(lk)
                if resolved:
                    links.append(resolved)

            # Prepend file stem + heading so embedding knows the source
            text = f"[{f.stem}]\n{part.strip()}"

            chunks.append({
                'id':      f"{rel}#{heading}",
                'file':    rel,
                'stem':    f.stem,
                'heading': heading,
                'text':    text[:1600],   # ~400 tokens — safe for MiniLM
                'links':   list(dict.fromkeys(links)),  # dedup, preserve order
            })

    return chunks, name_to_path


def main():
    print(f"Vault: {VAULT}")
    print("Collecting chunks...")
    chunks, name_map = collect_chunks()
    print(f"  {len(chunks)} chunks from {len(name_map)} notes")

    print("Loading embedding model (downloads ~80 MB on first run)...")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("\nMissing dependency. Run: pip install -r rag/requirements.txt")
        sys.exit(1)

    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Embedding... (takes ~30–90 seconds)")
    import numpy as np
    texts = [c['text'] for c in chunks]
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True,
                              convert_to_numpy=True)

    # L2-normalise so dot product == cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.clip(norms, 1e-9, None)

    payload = {
        'chunks':     chunks,
        'embeddings': embeddings.astype('float32'),
        'name_map':   name_map,
    }
    with open(INDEX_OUT, 'wb') as fh:
        pickle.dump(payload, fh)

    size_mb = INDEX_OUT.stat().st_size / 1024 / 1024
    print(f"\nIndex saved → {INDEX_OUT}  ({size_mb:.1f} MB)")
    print("\nQuery with:")
    print('  python rag/query.py "how does epoll work in the Reactor?"')


if __name__ == '__main__':
    main()
