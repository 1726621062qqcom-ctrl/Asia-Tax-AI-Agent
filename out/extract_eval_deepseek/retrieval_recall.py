"""Retrieval recall of the gold quotes (抽取改造.md §5 B acceptance), no model calls: for every disclosed row whose gold
quote lies inside some passage, is that passage among the top-k candidates? Channels bm25 / dense / fused (RRF),
query with or without the parties' names, k = 1, 3, 5, 8, 12, 20. Vectors come from the cache after the first run.

    python retrieval_recall.py [--cases a,b]
"""
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\Coding\Projects\TUM\project_study_self")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tax_graph.llm.extract import FieldSpec                 # noqa: E402
from tax_graph.llm.locate import RRF_K, PassageIndex, query_for   # noqa: E402
from tax_graph.quotes import loose                          # noqa: E402
import extract_eval as E                                     # noqa: E402
from extract_eval3 import load                               # noqa: E402

KS = (1, 3, 5, 8, 12, 20)


def fuse(lists):
    ranks = defaultdict(float)
    for lst in lists:
        for r, i in enumerate(lst):
            ranks[i] += 1.0 / (RRF_K + r)
    return [i for i, _ in sorted(ranks.items(), key=lambda t: -t[1])]


def main(argv):
    cases = argv[argv.index("--cases") + 1].split(",") if "--cases" in argv else list(E.CASES)
    tot, hit, nowhere = Counter(), Counter(), []
    per_field = defaultdict(Counter)
    for cid in cases:
        docs, specs, gold, _ = load(cid)
        idx = PassageIndex(docs, dense=True)
        normed = [loose(t) for t in idx.texts]
        for path, (kind, g, quote) in gold.items():
            if kind != "disclosed" or not quote:
                continue
            head = loose(quote[:80])
            where = {i for i, t in enumerate(normed) if head and head in t}
            if not where:
                nowhere.append((cid, path))
                continue
            tot["rows"] += 1
            s = specs[path]
            for vname, spec in (("base", FieldSpec(**dict(s.__dict__, about=""))), ("names", s)):
                q = query_for(spec)
                lists = {"bm25": idx.bm25(q, 50), "dense": idx.dense_search(q, 50)}
                lists["fused"] = fuse([lists["bm25"], lists["dense"]])
                for ch, lst in lists.items():
                    for k in KS:
                        if any(i in where for i in lst[:k]):
                            hit[(vname, ch, k)] += 1
                            if vname == "names" and ch == "fused":
                                per_field[path.split(".")[-1]][k] += 1
                if vname == "names":
                    per_field[path.split(".")[-1]]["rows"] += 1
    n = tot["rows"]
    print("disclosed rows with the gold quote inside a passage: %d; quote in no passage (spans two, or not verbatim): %d" % (n, len(nowhere)))
    for cid, path in nowhere:
        print("   nowhere:", cid, path)
    print()
    print("recall@k  %s" % "  ".join("k=%-3d" % k for k in KS))
    for vname in ("base", "names"):
        for ch in ("bm25", "dense", "fused"):
            print("%-6s %-6s %s" % (vname, ch, "  ".join("%5.2f" % (hit[(vname, ch, k)] / n) for k in KS)))
    print()
    print("names+fused by field: rows, then recall@k")
    for name, c in sorted(per_field.items()):
        print("  %-24s n=%2d  %s" % (name, c["rows"], "  ".join("%5.2f" % (c[k] / c["rows"]) for k in KS)))


if __name__ == "__main__":
    main(sys.argv)
