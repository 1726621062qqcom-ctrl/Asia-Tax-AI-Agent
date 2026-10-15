"""Consistency of the field dictionary: what the rules read versus what 信息收集.md names.

  python -m tax_graph.check_fields          (conda env "pytorch")

Reports, does not stop: (a) fields some rule reads that the document does not name — the document is behind the
rules; (b) document fields no rule reads — either dead weight or a rule still to write. Also prints, for scenario A,
the required and the still-missing fields (P2: computed per case, never a flat form).
"""
import io
import re
import sys
from pathlib import Path

from .cases import BASE_A, CASE_A, EVENT_A
from .scenarios import HOLDING
from .fields import DERIVED, fields, missing_fields, required_fields

DOC = Path(__file__).resolve().parents[1] / "信息收集.md"


def doc_fields():
    """Field names in the §3 and §4 tables: every backticked identifier in the field column."""
    text = DOC.read_text(encoding="utf-8")
    sec = text[text.index("## 3. CONDITIONAL"):text.index("## 5. 激活与收集")]
    names = set()
    for row in sec.splitlines():
        cells = [c.strip() for c in row.split("|")]
        if len(cells) < 4 or not cells[1].startswith("`") or cells[1] in ("`mount`",):
            continue
        col = cells[4] if len(cells) >= 6 else cells[2]
        for span in re.findall(r"`([^`]*)`", col):
            for name in span.split(","):
                name = re.sub(r"=.*$", "", name.strip())
                if re.fullmatch(r"[a-z_][a-z0-9_]*", name):
                    names.add(name)
    return names


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    read = fields()
    read_names = {k.split(".", 1)[1] for k in read}
    documented = doc_fields()
    derived = DERIVED
    inputs = {"cert_years", "circumstances_changed_on", "accrued_on", "actual", "parties_related",
              "delivered_to", "routed_via_trader", "shipped_from",                                         # decision D43               # consumed by facts.py / ex_post /
              "service_location", "accumulated_profits_share", "reduced_capital_ratio", "after_tax_profit",
              "wht_borne_by_payer", "cit_rate", "revenue", "total_assets", "employees",
              "incorporated_in", "managed_from", "senior_management_in_cn", "financial_hr_decisions_in_cn", "records_in_cn",
              "directors_majority_in_cn", "globe_income", "covered_taxes_other", "income_tax_other", "sbie", "payroll", "tangible_assets",
              "placed_by_plan", "gst_recovery_ratio", "service_onshore_share", "vat_borne_by_payer",
              "p2_negative_tax_election", "p2_carry_back_topup", "p2_qualified_cbcr", "p2_tcsh_history", "p2_cbcr_revenue",
              "p2_cbcr_pbt", "p2_cbcr_simplified_taxes", "p2_dm_avg_revenue_eur", "p2_dm_avg_income_eur", "p2_tcsh_elected",
              "p2_dm_elected", "p2_eur_rate", "p2_eur_rate_2027", "wound_up_by_plan", "unwind_step",
              "ip_book_value", "ip_book_amortization",
              "branch_profit_<j>", "branch_period_end_<j>", "branch_receipt_<j>", "branch_taxed_<j>",
              "lease_start", "lease_term_months", "annual_value",
              "taxable_income_other", "loss_brought_forward", "cn_loss_type", "cn_foreign_loss_offset",          # decision D51
              "cn_branch_actual_loss", "hk_loss_change_dominant_purpose", "sg_loss_shareholders_same",
              "sg_loss_continuity_waived", "sg_loss_same_trade", "sg_group_relief_elected"}   # engine / facts.py / losses inputs, not a rule's Leaf
    only_rules = sorted(read_names - documented - derived)
    only_doc = sorted(documented - read_names - inputs)
    out.write("fields read by rules: %d   named in 信息收集.md: %d   derived by facts.py: %d\n" % (len(read_names), len(documented), len(derived)))
    out.write("\nread by a rule, not in the document (%d):\n" % len(only_rules))
    for n in only_rules:
        out.write("  %-36s %s\n" % (n, ", ".join(sorted(r for k, rs in read.items() if k.endswith("." + n) for r in rs))[:90]))
    out.write("\nin the document, read by no rule (%d):\n" % len(only_doc))
    for n in only_doc:
        out.write("  %s\n" % n)
    g = HOLDING.build(EVENT_A, BASE_A, CASE_A)
    req, miss = required_fields(g), missing_fields(g)
    out.write("\nscenario A: %d required (flow, field) pairs, %d not stated or derived:\n" % (len(req), len(miss)))
    for fid, key in sorted(miss):
        out.write("  %-6s %s\n" % (fid, key))
    out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
