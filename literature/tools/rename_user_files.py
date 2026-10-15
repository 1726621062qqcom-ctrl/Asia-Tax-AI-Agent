#!/usr/bin/env python
"""One-off: give the files the user added by hand on 2026-10-05 the library's names.

Name: <ID>_<FirstAuthorSurname><Year>_<ShortTitle>[_preprint].pdf ("_preprint" marks a preprint or working paper).
E5 arrived as the whole LNAI 12882 volume; chapter 25 (PDF pages 269-278, printed 258-267) is cut out and the
volume is kept under _work/originals/. Every move is logged to _work/renames.csv with its sha256.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/rename_user_files.py [--dry-run]
"""
import csv
import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # literature/
RENAMES = [
    ("3473582.pdf", "A1_Merigoux2021_Catala.pdf"),
    ("3446804.3446850.pdf", "A2_Merigoux2021_FrenchTaxCompiler.pdf"),
    ("s10506-022-09328-5.pdf", "A3_Huttner2022_CatalaLegalExpertSystems.pdf"),
    ("ssrn-3088206.pdf", "A4_Lawsky2017_LogicForStatutes_preprint.pdf"),
    ("0004-37022990014-4.pdf", "A8_Reiter1980_DefaultReasoning.pdf"),
    ("3511265.3550447.pdf", "A9_Grimmelmann2022_PLandLaw.pdf"),
    ("FAIA-379-FAIA230962.pdf", "A11_Janatian2023_TextToStructure.pdf"),
    ("s10797-018-9491-6.pdf", "B1_vantRiet2018_OptimalTaxRouting.pdf"),
    ("s10797-018-9489-0.pdf", "B2_Hong2018_TreatiesFDINetwork.pdf"),
    ("s40844-018-0111-z.pdf", "B4_Nakamoto2018_ConduitJurisdictions.pdf"),
    ("s10797-012-9250-z.pdf", "B9_Weyzig2013_TreatyShoppingNL.pdf"),
    ("w24701.pdf", "B11_Torslov2018_MissingProfits_preprint.pdf"),
    ("Journal of Economic Surveys - 2019 - Beer - INTERNATIONAL CORPORATE TAX AVOIDANCE  A REVIEW OF THE CHANNELS  "
     "MAGNITUDES .pdf", "B12_Beer2020_CorporateTaxAvoidance.pdf"),
    ("1-s2.0-S0261560623001729-main.pdf", "B13_Damgaard2024_RealFDI.pdf"),
    ("2507.16126v1.pdf", "C6_Bock2025_TaxCalcBench_preprint.pdf"),
    ("2606.16118v2.pdf", "C8_Wang2026_KnowYourLimits_preprint.pdf"),
    ("2609.05928v1.pdf", "C9_Sadowski2026_SolvingVersusVerifying_preprint.pdf"),
    ("s10506-026-09525-6.pdf", "C10_Yadamsuren2026_StatutoryInconsistency.pdf"),
    ("rsta.2023.0159.pdf", "C12_Nay2024_LLMsAsTaxAttorneys.pdf"),
    ("ssrn-5939874.pdf", "D3_BlairStanek2025_ChatGPTNovelTaxStrategy.pdf"),
    ("s10506-016-9181-6.pdf", "D4_Hemberg2016_DetectingTaxEvasion.pdf"),
    ("1340132.pdf", "D5_McCarty1977_TAXMAN.pdf"),
    ("2594538.2594561.pdf", "E2_Libkin2014_IncompleteData.pdf"),
    ("2877206.pdf", "E3_Libkin2016_SQLThreeValuedLogic.pdf"),
    ("s10506-023-09376-5.pdf", "E6_Arias2024_SLAWDiscretion.pdf"),
    ("3462757.3466084.pdf", "E7_Morris2021_CASPLegislativeDrafting.pdf"),
    ("512950.512973.pdf", "E9_Cousot1977_AbstractInterpretation.pdf"),
    ("E10_SMUCCLaw2021_L4Docassemble.pdf", "E10_Morris2021_L4Docassemble.pdf"),
    ("Metamorphic_Testing_and_Debugging_of_Tax_Preparation_Software.pdf", "F1_TizpazNiari2023_MetamorphicTaxPrep.pdf"),
    ("3744916.3764575.pdf", "F3_GoganiKhiabani2026_LLMAgenticTaxPrep.pdf"),
    ("2504.18693v1.pdf", "F4_GoganiKhiabani2025_TaxPrepMaintenance_preprint.pdf"),
    ("A_Survey_on_Metamorphic_Testing.pdf", "F6_Segura2016_MetamorphicTestingSurvey.pdf"),
    ("3143561.pdf", "F7_Chen2018_MetamorphicTestingReview.pdf"),
]
E5_VOLUME = "978-3-030-85713-4.pdf"
E5_OUT = "E5_Arias2021_AdministrativeDiscretion.pdf"
E5_PAGES = (269, 278)                                # 1-based PDF pages of chapter 25 in the volume


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    dry = "--dry-run" in sys.argv
    rows, problems = [], []
    for old, new in RENAMES:
        src, dst = ROOT / old, ROOT / new
        if not src.exists():
            problems.append("missing: " + old)
        elif dst.exists():
            problems.append("target exists: " + new)
    if not (ROOT / E5_VOLUME).exists():
        problems.append("missing: " + E5_VOLUME)
    if problems:
        print("\n".join(problems))
        return 1
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for old, new in RENAMES:
        digest = sha256(ROOT / old)
        if not dry:
            (ROOT / old).rename(ROOT / new)
        rows.append({"at": stamp, "action": "rename", "old": old, "new": new, "sha256": digest})
    vol = ROOT / E5_VOLUME
    digest = sha256(vol)
    if not dry:
        import fitz
        src = fitz.open(str(vol))
        out = fitz.open()
        out.insert_pdf(src, from_page=E5_PAGES[0] - 1, to_page=E5_PAGES[1] - 1)
        out.save(str(ROOT / E5_OUT), garbage=3, deflate=True)
        out.close()
        src.close()
        keep = ROOT / "_work" / "originals"
        keep.mkdir(parents=True, exist_ok=True)
        shutil.move(str(vol), str(keep / E5_VOLUME))
    rows.append({"at": stamp, "action": "extract pages %d-%d" % E5_PAGES, "old": E5_VOLUME, "new": E5_OUT,
                 "sha256": digest})
    rows.append({"at": stamp, "action": "move", "old": E5_VOLUME, "new": "_work/originals/" + E5_VOLUME,
                 "sha256": digest})
    if not dry:
        log = ROOT / "_work" / "renames.csv"
        new_file = not log.exists()
        with log.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["at", "action", "old", "new", "sha256"])
            if new_file:
                w.writeheader()
            w.writerows(rows)
    for r in rows:
        print("%-22s %s -> %s" % (r["action"], r["old"][:60], r["new"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
