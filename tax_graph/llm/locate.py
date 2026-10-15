"""locate (抽取改造.md §5 B): candidate passages per field by retrieval, not by one long-context call.

    index = PassageIndex(docs)                       # docs: doc id -> text; passages cut at paragraph boundaries
    index.search("the acquisition cost ...", k=3)    # BM25 + BGE-M3 dense (cached) fused by reciprocal rank (RRF)

Why (literature/notes/M_综合.md): relevant text in the middle of a long context is used worse (M3), readers saturate
long before retrievers (M3), documents get harder with length (M13), and a model given the right passages reads
rather than recalls (M16). The library's own search uses the same three ingredients (official/tools/search.py:
BM25, BAAI/bge-m3, RRF with k=60); this module applies them to a case's documents in memory.

Passages keep their character offsets, so every candidate is a verbatim span of the document and the quote check
of extract.py holds by construction. BM25 tokenises Latin words and CJK bigrams; the dense channel is optional
(it needs sentence_transformers and the cached model), the model is loaded once per process, and its vectors are
cached by text hash in out/extract_vec_cache.sqlite so a passage is encoded once.
"""
import hashlib
import math
import re
import sqlite3
import threading
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
VEC_CACHE = ROOT / "out" / "extract_vec_cache.sqlite"
DENSE_MODEL = "BAAI/bge-m3"
RRF_K = 60
MAX_WORDS, OVERLAP = 120, 1                        # words per passage (CJK: characters / 2.5), paragraphs of overlap

_WORD = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")
_CJK = re.compile(r"[一-鿿]")
_MODEL = None                                      # the dense model, loaded once per process
_MODEL_LOCK = threading.RLock()                    # re-entrant: _encode holds it while _dense_model takes it again


def tokens(text: str) -> List[str]:
    t = text.lower()
    out = _WORD.findall(t)
    cjk = _CJK.findall(t)
    out += ["".join(p) for p in zip(cjk, cjk[1:])] if len(cjk) > 1 else cjk
    return out


def _paragraphs(text: str):
    """(start, end) of paragraphs: blank-line separated blocks; a PDF's single line breaks stay inside a block. A block
    longer than MAX_WORDS (a PDF page with no blank lines) is cut into runs of lines at a line that ends a sentence."""
    pos, out = 0, []
    for block in re.split(r"\n\s*\n", text):
        a = text.find(block, pos)
        if a < 0:
            a = pos
        b = a + len(block)
        pos = b
        if not block.strip():
            continue
        if _weight(block) <= MAX_WORDS:
            out.append((a, b))
            continue
        start, w = a, 0.0
        for m in re.finditer(r"[^\n]*\n?", block):
            line = m.group(0)
            if not line:
                continue
            w += _weight(line)
            ends = line.rstrip().endswith((".", "。", ":", ";", "：", "；", "!", "?"))
            if (w >= MAX_WORDS and ends) or w >= 2 * MAX_WORDS:
                out.append((start, a + m.end()))
                start, w = a + m.end(), 0.0
        if start < b and text[start:b].strip():
            out.append((start, b))
    return out


def _weight(s: str) -> float:
    return len(_WORD.findall(s.lower())) + len(_CJK.findall(s)) / 2.5


def passages(text: str):
    """Windows of whole paragraphs up to MAX_WORDS, one paragraph of overlap; (start, end) offsets into text."""
    paras = _paragraphs(text)
    out, i = [], 0
    while i < len(paras):
        j, w = i, 0.0
        while j < len(paras) and (w == 0 or w + _weight(text[paras[j][0]:paras[j][1]]) <= MAX_WORDS):
            w += _weight(text[paras[j][0]:paras[j][1]])
            j += 1
        out.append((paras[i][0], paras[j - 1][1]))
        i = max(i + 1, j - OVERLAP)
    return out


def _dense_model():
    global _MODEL
    with _MODEL_LOCK:
        if _MODEL is None:
            import os
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer(DENSE_MODEL)
            _MODEL.max_seq_length = min(_MODEL.max_seq_length or 512, 512)
    return _MODEL


def _encode(texts):
    with _MODEL_LOCK:                              # one encode at a time: the model is shared between threads
        return _dense_model().encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)


class PassageIndex:
    def __init__(self, docs: Dict[str, str], dense: bool = True, cache: Optional[Path] = VEC_CACHE):
        self.docs = docs
        self.items = []                              # (doc id, start, end)
        for did, text in docs.items():
            for a, b in passages(text):
                self.items.append((did, a, b))
        self.texts = [docs[d][a:b] for d, a, b in self.items]
        self._bm25()
        self.dense = dense
        self._vec = None
        self.cache = cache

    # ---------------------------------------------------------------- BM25 (Okapi)
    def _bm25(self, k1=1.5, b=0.75):
        self.tf = [Counter(tokens(t)) for t in self.texts]
        self.dl = [sum(c.values()) for c in self.tf]
        self.avgdl = (sum(self.dl) / len(self.dl)) if self.dl else 1.0
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(self.tf)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self.k1, self.b = k1, b

    def bm25(self, query: str, n=50):
        q = [t for t in set(tokens(query)) if t in self.idf]
        scores = []
        for i, c in enumerate(self.tf):
            s = 0.0
            for t in q:
                f = c.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        return [i for _, i in scores[:n]]

    # ---------------------------------------------------------------- dense (BGE-M3, cached)
    def _load_dense(self):
        import numpy as np
        import torch
        keys = [hashlib.sha1((DENSE_MODEL + "\n" + t).encode("utf-8")).hexdigest() for t in self.texts]
        have = {}
        con = None
        if self.cache:
            self.cache.parent.mkdir(parents=True, exist_ok=True)
            con = sqlite3.connect(str(self.cache), timeout=60)
            con.execute("CREATE TABLE IF NOT EXISTS vec (key TEXT PRIMARY KEY, dim INTEGER, vec BLOB)")
            for i in range(0, len(keys), 900):
                part = keys[i:i + 900]
                for k, dim, blob in con.execute("SELECT key, dim, vec FROM vec WHERE key IN (%s)" % ",".join("?" * len(part)), part):
                    have[k] = blob
        todo = [(k, t) for k, t in zip(keys, self.texts) if k not in have]
        for i in range(0, len(todo), 256):
            chunk = todo[i:i + 256]
            vecs = _encode([t for _, t in chunk])
            for (k, _), v in zip(chunk, vecs):
                have[k] = v.astype("float32").tobytes()
            if con is not None:
                con.executemany("INSERT OR REPLACE INTO vec VALUES (?,?,?)", [(k, vecs.shape[1], have[k]) for k, _ in chunk])
                con.commit()
        if con is not None:
            con.close()
        mat = np.vstack([np.frombuffer(have[k], dtype="float32") for k in keys]) if keys else np.zeros((0, 1), dtype="float32")
        self._vec = torch.from_numpy(mat.copy())

    def dense_search(self, query: str, n=50):
        if not self.dense or not self.texts:
            return []
        if self._vec is None:
            self._load_dense()
        import torch
        qv = torch.from_numpy(_encode([query])[0].astype("float32"))
        top = torch.topk(self._vec @ qv, min(n, self._vec.shape[0])).indices.tolist()
        return top

    # ---------------------------------------------------------------- fusion
    def search(self, query: str, k=3, n=50) -> List[dict]:
        ranks = defaultdict(dict)
        for name, hits in (("bm25", self.bm25(query, n)), ("dense", self.dense_search(query, n))):
            for r, i in enumerate(hits):
                ranks[i][name] = r
        fused = sorted(((sum(1.0 / (RRF_K + r) for r in ch.values()), i) for i, ch in ranks.items()), reverse=True)
        out = []
        for s, i in fused[:k]:
            did, a, b = self.items[i]
            out.append({"doc": did, "quote": self.texts[i], "start": a, "end": b, "score": round(s, 5),
                        "channels": sorted(ranks[i])})
        return out


def query_for(spec) -> str:
    """What the retriever looks for: the field's name words, meaning, unit, evidence hint, example phrasings and the
    parties it is about (names as written in the documents, " | " between parties, " / " between aliases)."""
    name = spec.key.rsplit(".", 1)[-1].replace("_", " ")
    parts = [name, spec.gloss, spec.unit, spec.hint, spec.examples, (spec.about or "").replace("|", " ").replace("/", " ")]
    return " ".join(p for p in parts if p)
