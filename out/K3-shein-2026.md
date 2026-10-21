# Question sheet: K3-shein-2026 (template holding)

No plan can be given yet: the data or confirmations below would change the chosen plan or its guaranteed tax. Answer only these; where you cannot, enter unknown (taken at its worst, never filled in).
Write the answers into `<case>.answers.json`: data (a value or {"value", "source"}), actions (yes / no / unknown), rulings (yes / no / unknown), library.

**Scope**: income tax only (decision D52). VAT, GST, stamp duty, customs duty, land appreciation tax, deed tax and property tax are not assessed; a case or a structure that attracts one of them is not handled. 14 candidate structures not compared for that reason: reorg (share transfer from HOLD to Roadget Business Pte. Ltd. / Roadget) attracts stamp duty in Hong Kong: a sale or purchase of Hong Kong stock is stamped under Head 2 of the First Schedule on each party (Cap. 117 s 4, s 19, Sch 1); reorg (share transfer from HOLD to Roadget Business Pte. Ltd. / Roadget) attracts stamp duty in Mainland China: a share transfer instrument executed in the Mainland, or executed abroad and used there, is a 产权转移书据 stamped at 0.05% of the price on each party (印花税法 第一条、第二条; 税目税率表); reorg (share transfer from HOLD to Roadget Business Pte. Ltd. / Roadget) attracts stamp duty in Singapore: a conveyance, assignment or transfer on sale of any stock or shares is stamped at 0.2% of the consideration (Stamp Duties Act First Schedule Article 3(c)); up1 (interest from Guangzhou Shein International Import & Export Co., Ltd. / Guangzhou Shein to HOLD) attracts VAT in Mainland China: a loan is a financial service; interest is the price of a service sold in the Mainland, taxed at 6% (增值税法 第三条、第四条、第十条); up1 (interest from Guangzhou Shein International Import & Export Co., Ltd. / Guangzhou Shein to Roadget Business Pte. Ltd. / Roadget) attracts VAT in Mainland China: a loan is a financial service; interest is the price of a service sold in the Mainland, taxed at 6% (增值税法 第三条、第四条、第十条).

## CN

| Kind | Address | Question | Value | Usual source | Impact |
|---|---|---|---|---|---|
| required (tax unbounded without it) | `OP.globe_income` | Please provide: the constituent entity's GloBE income in the Pillar Two sense (dividends and gains on disposal of holdings of 10% or more are generally excluded) (OP.globe_income) | amount | group Pillar Two computation workpapers | unbounded |

## SG

| Kind | Address | Question | Value | Usual source | Impact |
|---|---|---|---|---|---|
| required (tax unbounded without it) | `ULT.globe_income` | Please provide: the constituent entity's GloBE income in the Pillar Two sense (dividends and gains on disposal of holdings of 10% or more are generally excluded) (ULT.globe_income) | amount | group Pillar Two computation workpapers | unbounded |

16 candidate structures; 2 of them need the required data above before they can be computed.
