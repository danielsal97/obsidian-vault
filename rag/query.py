#!/usr/bin/env python3
"""
Query your Obsidian vault with natural language.

Requires:
    ANTHROPIC_API_KEY environment variable
    vault_index.pkl (run index.py first)

Usage:
    python rag/query.py "how does the Reactor dispatch to handlers?"
    python rag/query.py "walk me through what happens when malloc is called"
    python rag/query.py "why does LDS use UDP instead of TCP for minions?"
"""
import os
import sys
import pickle
import textwrap
from pathlib import Path

VAULT = Path(__file__).parent.parent
INDEX_FILE = Path(__file__).parent / 'vault_index.pkl'

TOP_K = 5          # primary semantic hits
LINK_HOPS = 1      # follow wiki-links N hops from each hit
MAX_LINKED = 4     # cap on extra linked chunks pulled in
CHUNK_PREVIEW = 700  # chars of linked-note preview (they are secondary)


# ── loading ──────────────────────────────────────────────────────────────────

def load_index():
    if not INDEX_FILE.exists():
        print("No index found. Run first:\n  python rag/index.py")
        sys.exit(1)
    with open(INDEX_FILE, 'rb') as fh:
        return pickle.load(fh)


# ── search ────────────────────────────────────────────────────────────────────

def semantic_search(query: str, index: dict, k: int = TOP_K):
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        print("Missing dependency. Run: pip install -r rag/requirements.txt")
        sys.exit(1)

    model = SentenceTransformer('all-MiniLM-L6-v2')
    q = model.encode([query], convert_to_numpy=True)
    q = q / max(float((q ** 2).sum() ** 0.5), 1e-9)

    import numpy as np
    scores = (index['embeddings'] @ q.T).flatten()
    top_idx = scores.argsort()[::-1][:k]
    return [(index['chunks'][i], float(scores[i])) for i in top_idx]


# ── link expansion ────────────────────────────────────────────────────────────

def first_chunk_for_file(file_path: str, index: dict):
    for chunk in index['chunks']:
        if chunk['file'] == file_path:
            return chunk
    return None


def expand_via_links(primary_hits, index):
    """Return additional chunks by following wiki-links from primary hits."""
    seen = {chunk['file'] for chunk, _ in primary_hits}
    extra = []

    for chunk, _ in primary_hits:
        for link_path in chunk['links'][:3]:          # top 3 links per chunk
            if link_path not in seen and len(extra) < MAX_LINKED:
                linked = first_chunk_for_file(link_path, index)
                if linked:
                    extra.append(linked)
                    seen.add(link_path)

    return extra


# ── context builder ───────────────────────────────────────────────────────────

def build_context(primary_hits, linked_chunks):
    parts = []

    parts.append("=== PRIMARY MATCHES ===")
    for chunk, score in primary_hits:
        parts.append(
            f"\n[{chunk['file']} § {chunk['heading']}]  (score {score:.2f})\n"
            f"{chunk['text']}"
        )

    if linked_chunks:
        parts.append("\n=== LINKED NOTES (via wiki-links) ===")
        for chunk in linked_chunks:
            parts.append(
                f"\n[{chunk['file']} § {chunk['heading']}]\n"
                f"{chunk['text'][:CHUNK_PREVIEW]}"
            )

    return '\n'.join(parts)


# ── claude ────────────────────────────────────────────────────────────────────

def ask_claude(question: str, context: str) -> str:
    try:
        import anthropic
    except ImportError:
        print("Missing dependency. Run: pip install -r rag/requirements.txt")
        sys.exit(1)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Set ANTHROPIC_API_KEY environment variable first.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    system = (
        "You are a systems engineering tutor. "
        "Answer using ONLY the vault notes provided as context. "
        "Be specific: cite component names, code paths, or mechanisms from the notes. "
        "Use the format: direct answer → why it works this way → runtime effect. "
        "If the notes don't cover part of the question, say so."
    )

    user = f"Vault context:\n\n{context}\n\n---\n\nQuestion: {question}"

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=1024,
        system=system,
        messages=[{'role': 'user', 'content': user}],
    )
    return msg.content[0].text


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    question = ' '.join(sys.argv[1:])

    print(f'\nQuery: "{question}"')
    print('Loading index...')
    index = load_index()
    chunk_count = len(index['chunks'])
    print(f'  {chunk_count} chunks indexed')

    print('Searching...')
    hits = semantic_search(question, index)
    linked = expand_via_links(hits, index)

    print(f'\nTop {TOP_K} matches:')
    for chunk, score in hits:
        print(f'  [{score:.3f}]  {chunk["file"]}  §  {chunk["heading"]}')

    if linked:
        print(f'\n+{len(linked)} linked notes pulled in:')
        for chunk in linked:
            print(f'  →  {chunk["file"]}  §  {chunk["heading"]}')

    context = build_context(hits, linked)

    print('\nAsking Claude...\n')
    print('─' * 64)
    answer = ask_claude(question, context)
    print(answer)
    print('─' * 64)

    print('\nSources:')
    seen = set()
    for chunk, _ in hits:
        if chunk['file'] not in seen:
            print(f'  {chunk["file"]}')
            seen.add(chunk['file'])


if __name__ == '__main__':
    main()
