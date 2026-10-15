#!/usr/bin/env python
"""Acceptance aid: print the parts of a paper card a reviewer must read, with lint flags.

Shown in full: claims (section 1), limitations, card notes, and result bullets without numbers (numbers are
covered by audit_cards.py, quotes by check_card.py). Result bullets with numbers are cut to their first 90
characters. Flags: wording that signals the card writer's own analysis, evaluative or judging words, and
claim or result bullets with no attribution to the authors or to a table or figure.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/review_view.py A1 [B3 ...]
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_card import CARDS, QUOTE, RESULTS, SECTIONS, check, doc_type_of, parse   # noqa: E402
from audit_cards import audit                                                          # noqa: E402

OWN = ["卡片自行", "卡片作者", "卡片编者", "自行相加", "自行计算", "自行统计", "按我的", "我的计算", "笔者", "本卡片计算",
       "由卡片", "逐格比较", "推算", "换算", "by my", "my arithmetic", "my count", "按表数字直接比较", "相加得", "合计得"]
JUDGE = ["看来", "显然", "明显", "笔误", "疑似", "似有误", "有误", "错误地", "夸大", "不严谨", "忽视", "忽略了", "未能充分",
         "过于", "问题在于", "然而作者", "但作者没有", "可惜", "不足", "仅仅", "竟", "居然", "值得", "应当", "应该"]
ATTR = ["作者", "文中", "原文", "论文", "文章", "本文", "报告", "称", "写道", "认为", "指出", "表示", "主张", "显示", "给出",
        "列出", "列", "表", "图", "Table", "Fig", "Figure", "实验", "发现", "假设", "提出", "定义", "描述", "说明", "记录",
        "文件", "规定", "条", "Art", "OECD", "Directive", "博文", "帖子", "post", "Post"]
LIMIT_SEC = {"research": "## 5. 作者陈述的局限与前提", "official": "## 4. 适用范围、生效与例外"}
NOTE_SEC = {"research": "## 8. 卡片说明", "official": "## 7. 卡片说明"}


def flags(text):
    plain = QUOTE.sub(" ", text)
    own = [w for w in OWN if w.lower() in plain.lower()]
    judge = [w for w in JUDGE if w in plain]
    return own, judge


def main():
    for i in sys.argv[1:]:
        fm, body, order, sec = parse((CARDS / (i + ".md")).read_text(encoding="utf-8"))
        dt = doc_type_of(i)
        errs, warns, st = check(i)
        checked, misses = audit(i)
        own, judge = flags(body)
        print("=" * 100)
        print("%s | %s | %s | read_scope %s | %d chars | checker E%d W%d Q%d | numbers %d, unmatched %d" % (
            i, fm.get("title", "")[:70], fm.get("version"), fm.get("read_scope"), len(body), len(errs), len(warns),
            st["quotes"], checked, len(misses)))
        for e in errs:
            print("  E " + e)
        for n, line in misses:
            print("  N %s <- %s" % (n, line[:90]))
        if own:
            print("  OWN-ANALYSIS words: %s" % own)
        if judge:
            print("  JUDGING words: %s" % judge)
        for h in SECTIONS[dt]:
            text = sec.get(h, "")
            if h == SECTIONS[dt][0] or h in (LIMIT_SEC[dt], NOTE_SEC[dt]):
                print("--- " + h)
                print(text)
            elif h == RESULTS[dt]:
                print("--- " + h + "  (bullets with numbers cut; numbers audited)")
                rows = 0
                for line in text.split("\n"):
                    if not line.strip():
                        continue
                    if line.lstrip().startswith("|"):
                        rows += 1                          # table rows: numbers are covered by audit_cards.py
                        continue
                    if rows:
                        print("  [%d table rows omitted]" % rows)
                        rows = 0
                    digits = re.search(r"\d", QUOTE.sub(" ", re.sub(r"\[(corr\.)?pp?\.[^\]]*\]", " ", line)))
                    unattributed = line.startswith("- ") and not any(a in line for a in ATTR)
                    mark = "  [UNATTRIBUTED?]" if unattributed else ""
                    print((line[:90] + " ...") if digits and len(line) > 90 else line, mark)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
