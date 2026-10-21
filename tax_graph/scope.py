"""Income tax only (decision D52, 2026-10-20).

The program handles a case only when every flow in it attracts income tax alone in the jurisdictions the flow touches:
the payer's and the payee's, the target company's for a share transfer, the property's for land or buildings. "Every
flow" includes the steps a plan would add (a share transfer that inserts or removes a holding company, a dividend
capitalised into share capital): a structure the program recommends must itself be within what it assesses.

OTHER_LEVIES says, per income kind and jurisdiction, which other levies that jurisdiction charges on such a flow, from
the charging provision; NONE says, for every remaining cell, why nothing else is charged. The table is written from the
law, not from the rule library: a kind is outside the scope even where the library has no rule for the levy, and a
library rule for a levy on an admitted kind is a defect (check_income_only). The library keeps its VAT, stamp and
property rules; the library-level harnesses (check_engine, data.gold, mutation, fingerprint) run them with scope=ALL,
the product-level ones (battery, check_planner, pipeline, page) under the policy.

    outside(graph)  -> the flows that attract another levy, each with the levy and its basis ([] = admitted)
    check(graph)    -> raises OutOfScope (a Reject) under the income-only policy
    kinds()         -> per income kind, where it is admitted: the hint the intake form shows
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .engine import Reject
from .model import (BRANCH_PROFIT, CAPITAL_REDUCTION, CN, DIVIDEND, GOODS, HK, INTEREST, IP_TRANSFER, JURISDICTIONS, LIQUIDATION,
                    PROPERTY, RENT, ROYALTY, SERVICE_FEE, SG, SHARE_TRANSFER)

ALL = "all"                       # the whole library: verification harnesses (battery, gold, grounding, mutation, planner checks)
INCOME_ONLY = "income_only"       # the product: intake, planner, page, CLI
POLICY = INCOME_ONLY
# the kinds the program handles under INCOME_ONLY; every other kind is paused (kept in the library, not offered, refused at the intake)
ADMITTED_KINDS = (DIVIDEND, INTEREST, CAPITAL_REDUCTION, LIQUIDATION, BRANCH_PROFIT)

LEVY_TEXT = {"vat": "VAT", "gst": "GST", "stamp": "stamp duty", "customs": "customs duty", "lat": "land appreciation tax",
             "deed": "deed tax", "property": "property tax", "paused": "a paused transaction kind"}
PAUSED_BASIS = "the program handles dividends, interest, capital reductions and liquidation distributions only; other kinds are paused"
JUR_TEXT = {CN: "Mainland China", HK: "Hong Kong", SG: "Singapore"}
KIND_TEXT = {DIVIDEND: "dividend", INTEREST: "interest", ROYALTY: "royalty", SERVICE_FEE: "service fee", SHARE_TRANSFER: "share transfer",
             LIQUIDATION: "liquidation distribution", CAPITAL_REDUCTION: "capital reduction", IP_TRANSFER: "IP ownership transfer",
             GOODS: "sale of goods", BRANCH_PROFIT: "branch profit", PROPERTY: "property sale", RENT: "property rent"}
KINDS = (DIVIDEND, INTEREST, ROYALTY, SERVICE_FEE, SHARE_TRANSFER, LIQUIDATION, CAPITAL_REDUCTION, IP_TRANSFER, GOODS, BRANCH_PROFIT,
         PROPERTY, RENT)


@dataclass(frozen=True)
class Levy:
    levy: str                                   # key of LEVY_TEXT
    basis: str                                  # the charging provision, in words
    cites: Tuple[str, ...]                      # library cite ids (doc#clause) or plain references
    when: Optional[Callable] = None             # (flow, graph) -> bool; None = always on this kind here
    when_text: str = ""                         # the condition in words, for the hint


def _capitalised_in_cn(f, g):
    return bool(f.attrs.get("capitalised")) and g.entities[f.payer].loc == CN


def _bank_lender(f, g):
    return g.entities[f.payee].type == "BANK_FI"


def _cross_border(f, g):
    return g.entities[f.payer].loc != g.entities[f.payee].loc


CN_VAT_SERVICE = Levy("vat", "a service or intangible sold in the Mainland (consumed there, or sold by a Mainland seller) is a taxable "
                      "transaction, taxed at 6% (增值税法 第三条、第四条、第十条)", ("cn.law.vat#3", "cn.law.vat#4", "cn.law.vat#10"))
CN_STAMP_EQUITY = Levy("stamp", "a share transfer instrument executed in the Mainland, or executed abroad and used there, is a 产权转移书据 "
                       "stamped at 0.05% of the price on each party (印花税法 第一条、第二条; 税目税率表)", ("cn.law.stamp#1", "cn.law.stamp#2", "cn.law.stamp.flk#20"))
HK_NONE = "Hong Kong levies no VAT or GST; stamp duty reaches only Hong Kong stock, immovable property and bearer instruments (Cap. 117 s 4, Sch 1)"
SG_GST_SERVICE = Levy("gst", "a supply of services by a Singapore supplier is standard-rated or zero-rated (GST Act s 8, s 21(3)); a service "
                      "imported by a Singapore recipient is reverse-charged (s 14), at the rate of s 16", ("sg.gsta1993.s14#s14", "sg.gsta1993.s16#s16"))
SG_NO_SUPPLY = "no supply for GST and no instrument in the Stamp Duties Act First Schedule"
CN_NO_INSTRUMENT = "a cash distribution is neither a sale (增值税法 第三条) nor an instrument in the 印花税税目税率表"

OTHER_LEVIES: Dict[Tuple[str, str], Tuple[Levy, ...]] = {
    # ---- Mainland China
    (DIVIDEND, CN): (Levy("stamp", "a dividend capitalised into share capital raises the paid-in capital on which the account-book stamp duty "
                          "is charged at 0.025% of the increase (印花税法 第十一条; 税目税率表 营业账簿)", ("cn.law.stamp.flk#11", "cn.law.stamp.flk#20"),
                          when=_capitalised_in_cn, when_text="when the dividend is capitalised into share capital"),),
    (INTEREST, CN): (Levy("vat", "a loan is a financial service; interest is the price of a service sold in the Mainland, taxed at 6% "
                          "(增值税法 第三条、第四条、第十条)", ("cn.law.vat#3", "cn.law.vat#4", "cn.law.vat#10")),
                     Levy("stamp", "a loan contract with a banking or other licensed financial institution is stamped at 0.005% of the "
                          "principal (印花税法 税目税率表 借款合同)", ("cn.law.stamp.flk#20",),
                          when=_bank_lender, when_text="when the lender is a banking or other licensed financial institution")),
    (ROYALTY, CN): (CN_VAT_SERVICE,),
    (SERVICE_FEE, CN): (CN_VAT_SERVICE,),
    (SHARE_TRANSFER, CN): (CN_STAMP_EQUITY,),
    (IP_TRANSFER, CN): (CN_VAT_SERVICE,
                        Levy("stamp", "a transfer of a trademark, copyright, patent or know-how is a 产权转移书据 stamped at 0.03% of the price on "
                             "each party (印花税法 税目税率表)", ("cn.law.stamp.flk#20",))),
    (GOODS, CN): (Levy("vat", "a sale of goods shipped from or located in the Mainland, and an import of goods, is a taxable transaction, "
                       "taxed at 13% (增值税法 第三条、第四条、第十条)", ("cn.law.vat#3", "cn.law.vat#4", "cn.law.vat#10")),
                  Levy("customs", "goods permitted to be imported or exported are subject to customs duty collected by Customs (关税法 第二条)",
                       ("cn.law.tariff#2", "cn.law.tariff#3"), when=_cross_border, when_text="when the goods cross the border")),
    (PROPERTY, CN): (Levy("vat", "a sale of immovable property located in the Mainland is a taxable transaction, taxed at 9% "
                          "(增值税法 第四条、第十条)", ("cn.law.vat#4", "cn.law.vat#10")),
                     Levy("lat", "the transferor of land use rights, buildings or attachments pays land appreciation tax on the gain "
                          "(土地增值税暂行条例 第二条)", ("cn.reg.lat#2",)),
                     Levy("deed", "the transferee of land or buildings in the Mainland pays deed tax (契税法 第一条)", ("cn.law.deed#1",)),
                     Levy("stamp", "a transfer instrument for land use rights or buildings is stamped at 0.05% of the price on each party "
                          "(印花税法 税目税率表 产权转移书据)", ("cn.law.stamp.flk#20",))),
    (RENT, CN): (Levy("vat", "the lease of immovable property located in the Mainland is a taxable transaction, taxed at 9% "
                      "(增值税法 第四条、第十条)", ("cn.law.vat#4", "cn.law.vat#10")),
                 Levy("property", "a let building is taxed on its rental income (房产税暂行条例 第三条)", ("cn.reg.property#3",)),
                 Levy("stamp", "a lease contract is stamped at 0.1% of the rent (印花税法 税目税率表 租赁合同)", ("cn.law.stamp.flk#20",))),
    # ---- Hong Kong
    (SHARE_TRANSFER, HK): (Levy("stamp", "a sale or purchase of Hong Kong stock is stamped under Head 2 of the First Schedule on each party "
                                "(Cap. 117 s 4, s 19, Sch 1)", ("hk.cap117.en#s4", "hk.cap117.en#s19", "hk.cap117.en#sch1")),),
    (PROPERTY, HK): (Levy("stamp", "a conveyance on sale of immovable property in Hong Kong is chargeable with ad valorem stamp duty under "
                          "Head 1(1) of the First Schedule (Cap. 117 s 4, Sch 1)", ("hk.cap117.en#s4", "hk.cap117.en#sch1")),),
    (RENT, HK): (Levy("property", "the owner of let land or buildings in Hong Kong is charged property tax on the net assessable value "
                      "(Cap. 112 s 5)", ("hk.cap112.en#s5",)),
                 Levy("stamp", "a lease of immovable property in Hong Kong is chargeable under Head 1(2) of the First Schedule (Cap. 117 s 4, Sch 1)",
                      ("hk.cap117.en#s4", "hk.cap117.en#sch1"))),
    # ---- Singapore
    (ROYALTY, SG): (SG_GST_SERVICE,),
    (SERVICE_FEE, SG): (SG_GST_SERVICE,),
    (IP_TRANSFER, SG): (SG_GST_SERVICE,),
    (SHARE_TRANSFER, SG): (Levy("stamp", "a conveyance, assignment or transfer on sale of any stock or shares is stamped at 0.2% of the "
                                "consideration (Stamp Duties Act First Schedule Article 3(c))", ("sg.sda1929.sch1#sch1",)),),
    (GOODS, SG): (Levy("gst", "a supply of goods made in Singapore, and an import of goods, is chargeable with GST (GST Act s 8) at the "
                       "rate of s 16", ("sg.gsta1993.s16#s16",)),),
    (PROPERTY, SG): (Levy("stamp", "a conveyance on sale of immovable property is stamped under Article 3(a) of the First Schedule, with the "
                          "buyer's and seller's additional duties where they apply (Stamp Duties Act First Schedule)", ("sg.sda1929.sch1#sch1",)),
                     Levy("gst", "a sale of non-residential property is a taxable supply (GST Act s 8) at the rate of s 16", ("sg.gsta1993.s16#s16",))),
    (RENT, SG): (Levy("property", "the owner of a let property is charged property tax on its annual value (Property Tax Act s 6, rates in s 9)",
                      ("sg.pta1960.s9#all",)),
                 Levy("gst", "the letting of non-residential property is a taxable supply (GST Act s 8) at the rate of s 16", ("sg.gsta1993.s16#s16",)),
                 Levy("stamp", "a lease is stamped under Article 8 of the First Schedule (Stamp Duties Act First Schedule)", ("sg.sda1929.sch1#sch1",))),
}

NONE: Dict[Tuple[str, str], str] = {           # the cells where nothing but income tax is charged, with the reason
    (DIVIDEND, CN): CN_NO_INSTRUMENT + " (a capitalised dividend: see OTHER_LEVIES)",
    (LIQUIDATION, CN): CN_NO_INSTRUMENT,
    (CAPITAL_REDUCTION, CN): CN_NO_INSTRUMENT + "; the account-book duty is charged on increases only (印花税法 第十一条)",
    (BRANCH_PROFIT, CN): "a branch's profit attribution is no transaction: no sale, no instrument",
    (DIVIDEND, HK): HK_NONE, (INTEREST, HK): HK_NONE, (ROYALTY, HK): HK_NONE, (SERVICE_FEE, HK): HK_NONE, (LIQUIDATION, HK): HK_NONE,
    (CAPITAL_REDUCTION, HK): HK_NONE, (IP_TRANSFER, HK): HK_NONE, (BRANCH_PROFIT, HK): HK_NONE,
    (GOODS, HK): HK_NONE + "; the excise on dutiable commodities (Cap. 109: liquor, tobacco, hydrocarbon oil, methyl alcohol) is not represented",
    (DIVIDEND, SG): SG_NO_SUPPLY, (LIQUIDATION, SG): SG_NO_SUPPLY, (CAPITAL_REDUCTION, SG): SG_NO_SUPPLY, (BRANCH_PROFIT, SG): SG_NO_SUPPLY,
    (INTEREST, SG): "the provision of a loan, advance or credit is an exempt supply (GST Act Fourth Schedule Part I para 1(g)); a plain loan "
                    "agreement is not an instrument in the Stamp Duties Act First Schedule (a mortgage would be)",
}


@dataclass
class Outside:
    flow: str                                   # the flow id as the graph names it (repeats of a year collapse onto the first)
    income: str
    jur: str
    levy: str
    basis: str
    cites: Tuple[str, ...]
    when_text: str = ""
    payer: str = ""
    payee: str = ""

    def text(self, names=None):
        n = names or {}
        if self.levy == "paused":
            return "%s (%s from %s to %s) is a paused transaction kind: %s" % (
                self.flow, KIND_TEXT.get(self.income, self.income), n.get(self.payer, self.payer), n.get(self.payee, self.payee), self.basis)
        return "%s (%s from %s to %s) attracts %s in %s%s: %s" % (
            self.flow, KIND_TEXT.get(self.income, self.income), n.get(self.payer, self.payer), n.get(self.payee, self.payee),
            LEVY_TEXT.get(self.levy, self.levy), JUR_TEXT.get(self.jur, self.jur), (" " + self.when_text) if self.when_text else "", self.basis)

    def json(self, names=None):
        return {"flow": self.flow, "income": self.income, "jurisdiction": self.jur, "levy": LEVY_TEXT.get(self.levy, self.levy),
                "basis": self.basis, "cites": list(self.cites), "when": self.when_text, "text": self.text(names)}


class OutOfScope(Reject):
    """The case, or the candidate structure, attracts a levy other than income tax (decision D52)."""


def active(scope=None):
    return (scope or POLICY) == INCOME_ONLY


def touched(flow, graph):
    """The jurisdictions a flow touches: both parties; the target company of a share transfer; where a property lies."""
    locs = {graph.entities[flow.payer].loc, graph.entities[flow.payee].loc}
    if flow.target and flow.target in graph.entities:
        locs.add(graph.entities[flow.target].loc)
    if flow.income in (PROPERTY, RENT) and flow.attrs.get("property_loc"):
        locs.add(flow.attrs["property_loc"])
    return {x for x in locs if x}


def levies_of(flow, graph) -> List[Tuple[str, Levy]]:
    """The other levies a flow attracts, by the law, as (jurisdiction, Levy)."""
    out = []
    for jur in sorted(touched(flow, graph), key=lambda j: JURISDICTIONS.index(j) if j in JURISDICTIONS else 9):
        for lv in OTHER_LEVIES.get((flow.income, jur), ()):
            if lv.when is None or lv.when(flow, graph):
                out.append((jur, lv))
    return out


def outside(graph) -> List[Outside]:
    """Every (flow, jurisdiction, levy) the graph attracts beyond income tax; [] when the graph is admitted."""
    seen, out = set(), []
    for f in graph.flows:
        base = f.id.split("@", 1)[0]
        if f.income not in ADMITTED_KINDS:
            if (base, "", "paused") not in seen:
                seen.add((base, "", "paused"))
                out.append(Outside(base, f.income, "", "paused", PAUSED_BASIS, (), "", f.payer, f.payee))
            continue
        for jur, lv in levies_of(f, graph):
            key = (base, jur, lv.levy)
            if key in seen:
                continue
            seen.add(key)
            out.append(Outside(base, f.income, jur, lv.levy, lv.basis, lv.cites, lv.when_text, f.payer, f.payee))
    return out


def compact(whys: List[dict]) -> str:
    """Outside.json rows -> 'reorg (share transfer): stamp duty in Mainland China, Hong Kong; up1 (interest): VAT in Mainland China'."""
    by = {}
    for w in whys:
        by.setdefault((w["flow"], w["income"]), {}).setdefault((w["levy"], w["when"]), []).append(w["jurisdiction"])

    def one(l, wh, js):
        if l == LEVY_TEXT["paused"]:
            return "paused kind"
        return "%s in %s%s" % (l, ", ".join(dict.fromkeys(js)), (" " + wh) if wh else "")
    return "; ".join("%s (%s): %s" % (f, KIND_TEXT.get(i, i), ", ".join(one(l, wh, js) for (l, wh), js in d.items())) for (f, i), d in by.items())


def reason(items: List[Outside], names=None) -> str:
    """One message per refused graph: each flow once, its levies grouped, the charging provisions after them."""
    n = names or {}
    by = {}
    for x in items:
        by.setdefault((x.flow, x.income, x.payer, x.payee), {}).setdefault((x.levy, x.when_text), []).append(x)
    parts = []
    for (flow, income, payer, payee), d in by.items():
        if ("paused", "") in d:
            parts.append(d[("paused", "")][0].text(n))
            continue
        lv = ["%s in %s%s (%s)" % (LEVY_TEXT[levy], ", ".join(JUR_TEXT.get(y.jur, y.jur) for y in ys), (" " + when) if when else "",
                                   "; ".join(dict.fromkeys(y.basis for y in ys))) for (levy, when), ys in d.items()]
        parts.append("%s (%s from %s to %s) attracts %s" % (flow, KIND_TEXT.get(income, income), n.get(payer, payer), n.get(payee, payee), "; ".join(lv)))
    return "outside the scope of this program (income tax only): " + "; ".join(parts)


def check(graph, scope=None, names=None):
    """Raise OutOfScope under the income-only policy when the graph attracts another levy; return the graph otherwise."""
    if active(scope):
        items = outside(graph)
        if items:
            raise OutOfScope(reason(items, names))
    return graph


def kinds() -> Dict[str, dict]:
    """Per income kind: the jurisdictions where another levy arises (with the levies), whether the kind is admitted
    everywhere, and a one-line hint for the intake form."""
    out = {}
    for kind in KINDS:
        if kind not in ADMITTED_KINDS:
            out[kind] = {"label": KIND_TEXT[kind], "admitted_everywhere": False, "levies": {}, "hint": "paused: not handled"}
            continue
        by_jur = {}
        for jur in JURISDICTIONS:
            lvs = OTHER_LEVIES.get((kind, jur), ())
            if lvs:
                by_jur[jur] = [{"levy": LEVY_TEXT[l.levy], "when": l.when_text} for l in lvs]
        always = [j for j, lvs in by_jur.items() if any(not x["when"] for x in lvs)]
        parts = []
        for jur, lvs in by_jur.items():
            names_ = ", ".join(x["levy"] + ((" " + x["when"]) if x["when"] else "") for x in lvs)
            parts.append("%s (%s)" % (JUR_TEXT[jur], names_))
        if not always:
            hint = "income tax only in all three jurisdictions"
        elif len(always) == len(JURISDICTIONS):
            hint = "not handled: " + "; ".join(parts)
        else:
            hint = "not handled when a party is in %s" % "; ".join(p for p in parts if p.split(" (")[0] in {JUR_TEXT[j] for j in always})
        out[kind] = {"label": KIND_TEXT[kind], "admitted_everywhere": not by_jur, "levies": by_jur, "hint": hint}
    return out


def table() -> List[dict]:
    """Every (kind, jurisdiction) cell with its levies or its declared reason for none: the documentation and the check."""
    rows = []
    for kind in KINDS:
        for jur in JURISDICTIONS:
            lvs = OTHER_LEVIES.get((kind, jur), ())
            rows.append({"income": kind, "jur": jur, "levies": [l.levy for l in lvs], "conditional": [l.when_text for l in lvs if l.when],
                         "none": NONE.get((kind, jur), ""), "declared": bool(lvs) or (kind, jur) in NONE})
    return rows
