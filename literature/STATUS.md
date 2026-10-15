# STATUS

由 `tools/build_manifest.py` 生成，不要手改。逐条细节见 `manifest.csv`，论文卡片见 `paper_cards/`。

| 项 | 数量 |
|---|---|
| 清单条目（A–G） | 71 |
| 有文件 | 67 |
| 　其中发表版 | 61 |
| 　其中预印本或工作论文 | 6 |
| 　其中由用户手动下载 | 33 |
| 缺失 | 4 |
| 校验问题 | 0 |

## 缺失

| id | 题目 | 说明 | 链接 |
|---|---|---|---|
| A5 | Formalizing the Code | 无 DOI，期刊无自有在线 PDF；发表版需经 HeinOnline 或 Westlaw（70 Tax L. Rev. 377）。SSRN 2987065 是工作论文版，按规则不下；用户确认找不到即放弃（2026-10-05） |  |
| B10 | The Indirect Side of Direct Investment: Multinational Company Finance and Taxation | 图书；章节 DOI 前缀 10.7551/mitpress/8710，需机构订阅或纸本；用户确认找不到即放弃（2026-10-05） | https://direct.mit.edu/books/monograph/2459 |
| B14 | Conduit countries and treaty shopping | Edward Elgar 手册章节，需订阅；用户确认找不到即放弃（2026-10-05） | https://doi.org/10.4337/9781803929743.00021 |
| E1 | Introduction to Metamathematics | 图书，无 DOI；需馆藏纸本或电子书；用户确认找不到即放弃（2026-10-05） |  |

## 预印本或工作论文（不是发表版）

| id | 文件 | 页数 | 说明 |
|---|---|---|---|
| A4 ★ | `A4_Lawsky2017_LogicForStatutes_preprint.pdf` | 19 | 文件为 SSRN 预印本（标注 Florida Tax Review, forthcoming；Northwestern Public Law and Legal Theory Series No. 17-28），页码与发表版 21(1), 60–80 不同；发表版需登录，用户采用预印本 |
| B11 | `B11_Torslov2018_MissingProfits_preprint.pdf` | 56 | 文件为 NBER 工作论文 24701（2018-06，2020-04 修订），不是 RES 发表版；用户采用工作论文版 |
| C6 | `C6_Bock2025_TaxCalcBench_preprint.pdf` | 15 | 截至 2026-10-05 只有 arXiv 预印本（DataCite DOI），用户采用预印本 |
| C8 | `C8_Wang2026_KnowYourLimits_preprint.pdf` | 17 | 截至 2026-10-05 只有 arXiv 预印本（DataCite DOI），用户采用预印本；文件为 v2，首页注明 Preprint. Under review. |
| C9 | `C9_Sadowski2026_SolvingVersusVerifying_preprint.pdf` | 12 | 截至 2026-10-05 只有 arXiv 预印本（DataCite DOI），用户采用预印本；清单称该文属 ICTAI 2026，本 PDF 与已查到的记录都未能确认，ICTAI 2026 论文集尚未出版 |
| F4 | `F4_GoganiKhiabani2025_TaxPrepMaintenance_preprint.pdf` | 18 | 截至 2026-10-05 只有 arXiv 预印本（DataCite DOI），用户采用预印本 |

## 发表版

| id | 文件 | 页数 | 来源 | 链接 |
|---|---|---|---|---|
| A1 ★ | `A1_Merigoux2021_Catala.pdf` | 29 | 用户 | https://doi.org/10.1145/3473582 |
| A2 | `A2_Merigoux2021_FrenchTaxCompiler.pdf` | 12 | 用户 | https://doi.org/10.1145/3446804.3446850 |
| A3 | `A3_Huttner2022_CatalaLegalExpertSystems.pdf` | 24 | 用户 | https://doi.org/10.1007/s10506-022-09328-5 |
| A6 | `A6_Lawsky2022_CodingTheCode.pdf` | 25 | 脚本 | https://doi.org/10.25172/smulr.75.3.4 |
| A7 | `A7_Sergot1986_BritishNationalityAct.pdf` | 17 | 脚本 | https://doi.org/10.1145/5689.5920 |
| A8 | `A8_Reiter1980_DefaultReasoning.pdf` | 52 | 用户 | https://doi.org/10.1016/0004-3702(80)90014-4 |
| A9 | `A9_Grimmelmann2022_PLandLaw.pdf` | 11 | 用户 | https://doi.org/10.1145/3511265.3550447 |
| A10 | `A10_Lorenzo2025_TaxLawToCode.pdf` | 17 | 脚本 | https://doi.org/10.18653/v1/2025.nllp-1.4 |
| A11 | `A11_Janatian2023_TextToStructure.pdf` | 10 | 用户 | https://doi.org/10.3233/FAIA230962 |
| B1 ★ | `B1_vantRiet2018_OptimalTaxRouting.pdf` | 51 | 用户 | https://doi.org/10.1007/s10797-018-9491-6 |
| B2 ★ | `B2_Hong2018_TreatiesFDINetwork.pdf` | 44 | 用户 | https://doi.org/10.1007/s10797-018-9489-0 |
| B3 | `B3_Park2021_TreatyShoppingRoutes.pdf` | 16 | 脚本 | https://doi.org/10.1371/journal.pone.0256764 |
| B3 | `B3_Park2021_TreatyShoppingRoutes_correction.pdf` | | 脚本 | https://doi.org/10.1371/journal.pone.0269581 |
| B4 | `B4_Nakamoto2018_ConduitJurisdictions.pdf` | 17 | 用户 | https://doi.org/10.1007/s40844-018-0111-z |
| B5 | `B5_GarciaBernardo2017_OffshoreFinancialCenters.pdf` | 10 | 脚本 | https://doi.org/10.1038/s41598-017-06322-9 |
| B6 | `B6_Petkova2020_RelevanceDTTs.pdf` | 31 | 脚本 | https://doi.org/10.1007/s10797-019-09570-9 |
| B7 | `B7_Petkova2021_WHTRatesDividends.pdf` | 51 | 脚本 | https://doi.org/10.1007/s10797-020-09637-y |
| B8 | `B8_vantRiet2025_TreatyShoppingGlobalMinTax.pdf` | 63 | 脚本 | https://doi.org/10.1177/10911421251334849 |
| B9 | `B9_Weyzig2013_TreatyShoppingNL.pdf` | 28 | 用户 | https://doi.org/10.1007/s10797-012-9250-z |
| B12 | `B12_Beer2020_CorporateTaxAvoidance.pdf` | 29 | 用户 | https://doi.org/10.1111/joes.12305 |
| B13 | `B13_Damgaard2024_RealFDI.pdf` | 25 | 用户 | https://doi.org/10.1016/j.jimonfin.2023.102971 |
| C1 ★ | `C1_Holzenberger2020_SARA.pdf` | 8 | 脚本 | https://ceur-ws.org/Vol-2645/paper5.pdf |
| C2 | `C2_Holzenberger2021_FactoringStatutoryReasoning.pdf` | 17 | 脚本 | https://doi.org/10.18653/v1/2021.acl-long.213 |
| C3 | `C3_BlairStanek2023_GPT3StatutoryReasoning.pdf` | 11 | 脚本 | https://doi.org/10.1145/3594536.3595163 |
| C4 | `C4_Holzenberger2023_SymbolicStatutoryReasoning.pdf` | 19 | 脚本 | https://doi.org/10.18653/v1/2023.nllp-1.12 |
| C5 ★ | `C5_Jurayj2026_LMLogicProgramsTax.pdf` | 11 | 脚本 | https://doi.org/10.1609/aaai.v40i45.41212 |
| C7 | `C7_Kordjamshidi2026_ReasonersOrTranslators.pdf` | 17 | 脚本 | https://doi.org/10.18653/v1/2026.surgellm-1.23 |
| C10 | `C10_Yadamsuren2026_StatutoryInconsistency.pdf` | 35 | 用户 | https://doi.org/10.1007/s10506-026-09525-6 |
| C11 | `C11_Guha2023_LegalBench.pdf` | 157 | 脚本 | https://doi.org/10.52202/075280-1915 |
| C12 | `C12_Nay2024_LLMsAsTaxAttorneys.pdf` | 15 | 用户 | https://doi.org/10.1098/rsta.2023.0159 |
| C13 | `C13_Pan2023_LogicLM.pdf` | 19 | 脚本 | https://doi.org/10.18653/v1/2023.findings-emnlp.248 |
| C14 | `C14_Olausson2023_LINC.pdf` | 24 | 脚本 | https://doi.org/10.18653/v1/2023.emnlp-main.313 |
| C15 | `C15_Hendrycks2021_CUAD.pdf` | 10 | 脚本 | https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/6ea9ab1baa0efb9e19094440c317e21b-Abstract-round1.html |
| C16 | `C16_GoganiKhiabani2025_LLMsOnVITATest.pdf` | 22 | 脚本 | https://doi.org/10.1007/s10506-025-09465-7 |
| C17 | `C17_Padhye2024_AIDrivenStatutoryReasoning.pdf` | 16 | 脚本 | https://law.mit.edu/pub/aidrivenstatutoryreasoning |
| D1 ★ | `D1_BlairStanek2022_ShelterCheck.pdf` | 11 | 脚本 | https://hal.science/hal-04462115 |
| D2 ★ | `D2_BlairStanek2026_LLMsIdentifyTaxAbuse.pdf` | 9 | 脚本 | https://doi.org/10.1609/aaai.v40i45.41165 |
| D3 | `D3_BlairStanek2025_ChatGPTNovelTaxStrategy.pdf` | 5 | 用户 | https://www.taxnotes.com/tax-notes-today-federal/artificial-intelligence/chatgpt-generates-novel-tax-strategy/2025/11/14/7t8mv |
| D4 | `D4_Hemberg2016_DetectingTaxEvasion.pdf` | 34 | 用户 | https://doi.org/10.1007/s10506-016-9181-6 |
| D5 | `D5_McCarty1977_TAXMAN.pdf` | 58 | 用户 | https://doi.org/10.2307/1340132 |
| E2 ★ | `E2_Libkin2014_IncompleteData.pdf` | 13 | 用户 | https://doi.org/10.1145/2594538.2594561 |
| E3 | `E3_Libkin2016_SQLThreeValuedLogic.pdf` | 28 | 用户 | https://doi.org/10.1145/2877206 |
| E4 | `E4_Arias2018_CASPWithoutGrounding.pdf` | 18 | 脚本 | https://doi.org/10.1017/S1471068418000285 |
| E5 ★ | `E5_Arias2021_AdministrativeDiscretion.pdf` | 10 | 用户 | https://doi.org/10.1007/978-3-030-85713-4_25 |
| E6 | `E6_Arias2024_SLAWDiscretion.pdf` | 24 | 用户 | https://doi.org/10.1007/s10506-023-09376-5 |
| E7 | `E7_Morris2021_CASPLegislativeDrafting.pdf` | 2 | 用户 | https://doi.org/10.1145/3462757.3466084 |
| E8 | `E8_Kowalski2022_LogicalEnglishSwaps.pdf` | 35 | 脚本 | https://doi.org/10.1007/s10506-021-09295-3 |
| E9 | `E9_Cousot1977_AbstractInterpretation.pdf` | 15 | 用户 | https://doi.org/10.1145/512950.512973 |
| E10 | `E10_Morris2021_L4Docassemble.pdf` | 15 | 脚本 | https://medium.com/computational-law-diary/introducing-l4-docassemble-69ce4b1fb1e7 |
| F1 ★ | `F1_TizpazNiari2023_MetamorphicTaxPrep.pdf` | 12 | 用户 | https://doi.org/10.1109/ICSE-SEIS58686.2023.00019 |
| F2 | `F2_Srinivas2023_FewShotMetamorphicSpecs.pdf` | 14 | 脚本 | https://doi.org/10.18653/v1/2023.nllp-1.23 |
| F3 | `F3_GoganiKhiabani2026_LLMAgenticTaxPrep.pdf` | 12 | 用户 | https://doi.org/10.1145/3744916.3764575 |
| F5 | `F5_Goutagny2025_CUTECat.pdf` | 31 | 脚本 | https://doi.org/10.1007/978-3-031-91121-7_2 |
| F6 | `F6_Segura2016_MetamorphicTestingSurvey.pdf` | 20 | 用户 | https://doi.org/10.1109/TSE.2016.2532875 |
| F7 | `F7_Chen2018_MetamorphicTestingReview.pdf` | 27 | 用户 | https://doi.org/10.1145/3143561 |
| F8 | `F8_Barr2015_OracleProblem.pdf` | 19 | 脚本 | https://doi.org/10.1109/TSE.2014.2372785 |
| F9 | `F9_Claessen2000_QuickCheck.pdf` | 12 | 脚本 | https://doi.org/10.1145/351240.351266 |
| G1 | `G1_OECD2015_BEPSAction6.pdf` | 106 | 脚本 | https://doi.org/10.1787/9789264241695-en |
| G2 | `G2_OECD2016_MLI.pdf` | 49 | 脚本 | https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/multilateral-convention-to-implement-tax-treaty-related-measures-to-prevent-beps.pdf |
| G3 | `G3_OECD2013_TRACE.pdf` | 135 | 脚本 | https://doi.org/10.1787/0bb7b24d-en |
| G4 | `G4_EU2025_FASTERDirective.pdf` | 32 | 脚本 | https://eur-lex.europa.eu/eli/dir/2025/50/oj/eng |
| G5 | `G5_Mohun2020_CrackingTheCode.pdf` | 110 | 脚本 | https://doi.org/10.1787/3afe6ba5-en |

## 与清单不符之处

- **A4**：补全：Florida Tax Review 21(1), 60–80, DOI 10.5744/ftr.2017.0002（出版日期 2017-12-19；UF 法学院仓储标为 2018）
- **A5**：补全：70 Tax L. Rev. 377 (2017)；期刊版无 DOI
- **A6**：补全：DOI 10.25172/smulr.75.3.4
- **A9**：作者确认：James Grimmelmann（单一作者）
- **A11**：补全：JURIX 2023 收于 Frontiers in Artificial Intelligence and Applications 379，DOI 10.3233/FAIA230962
- **B2**：补全：DOI 10.1007/s10797-018-9489-0
- **B3**：更正一文：PLoS ONE 17(6): e0269581 (2022), DOI 10.1371/journal.pone.0269581，已一并下载
- **B4**：已正式发表：Evolutionary and Institutional Economics Review, 2018, DOI 10.1007/s40844-018-0111-z；发表版题目把 Countries 改为 Jurisdictions
- **B5**：补全：Scientific Reports 7, 6246 (2017)
- **B7**：补全：DOI 10.1007/s10797-020-09637-y（2020-12 在线发表）
- **B9**：题目全称：…structural determinants of Foreign Direct Investment routed through the Netherlands；2012 年在线发表，2013 年刊出 20(6)
- **B12**：2019 年在线发表，2020 年刊出 34(3), 660–688
- **B13**：清单列的是 IMF 工作论文 19/274；发表版是 Journal of International Money and Finance 140 (2024) 102971, DOI 10.1016/j.jimonfin.2023.102971
- **B14**：作者：Alfons J. Weichenrieder, Dmitry Erokhin；第 12 章，pp. 218–237，2024
- **C1**：补全：CEUR Workshop Proceedings Vol-2645, pp. 31–38；无 DOI
- **C4**：作者确认：Nils Holzenberger, Benjamin Van Durme
- **C7**：已正式发表：ACL 2026 的 SURGeLLM 研讨会论文集，DOI 10.18653/v1/2026.surgellm-1.23；发表版题目末尾与预印本不同（…Robustness on …），以 DOI 记录为准
- **C10**：已正式发表：Artificial Intelligence and Law, 2026-07 在线，DOI 10.1007/s10506-026-09525-6；发表版题目改为 LLM-assisted formalization for deterministic detection of statutory inconsistency in tax law
- **C11**：补全：Advances in Neural Information Processing Systems 36, pp. 44123–44279, DOI 10.52202/075280-1915
- **C12**：已正式发表：Philosophical Transactions of the Royal Society A 382(2270): 20230159 (2024)；作者：John J. Nay, David Karamardian, Sarah B. Lawsky, Wenting Tao, Meghana Bhat, Raghav Jain, Aaron Travis Lee, Jonathan H. Choi, Jungo Kasai
- **C14**：作者：Theo X. Olausson, Alex Gu, Benjamin Lipkin, Cedegao E. Zhang, Armando Solar-Lezama, Joshua B. Tenenbaum, Roger Levy
- **C16**：作者：Sina Gogani-Khiabani, Ashutosh Trivedi, ShinPing Chyi, Saeid Tizpaz-Niari
- **C17**：作者：Rohan Padhye（PDF 首页误印为 Padye）；2024-09-10 发表；无 DOI
- **D1**：补全：Tax Notes Federal 177 (Dec. 12, 2022), p. 1515 起
- **D2**：确认发表于 AAAI 2026：Proceedings of the AAAI Conference on Artificial Intelligence 40(45), 38261–38269
- **D3**：作者：Andrew Blair-Stanek, Nils Holzenberger, Benjamin Van Durme；出处：Tax Notes Federal 189 (Nov. 17, 2025), 1097–1101；Tax Notes Today Federal 网络版 2025-11-14（清单写 2025-11-13）
- **D5**：补全：Harvard Law Review 90(5), 837–893；JSTOR DOI 10.2307/1340132；作者全名 L. Thorne McCarty
- **E2**：完整题目：Incomplete data: what went wrong, and how to fix it；PODS 2014, pp. 1–13
- **E6**：2023 年在线发表，刊出于 32(4), 1141–1164 (2024)
- **E7**：ICAIL 2021, pp. 262–263（两页扩展摘要）
- **E8**：2021 年在线发表，刊出于 30(2), 163–197 (2022)
- **E9**：POPL '77, pp. 238–252
- **E10**：作者：Jason Morris（SMU Centre for Computational Law），2021-05-05 发表于 Medium
- **F1**：补全：ICSE-SEIS 2023, pp. 138–149, DOI 10.1109/ICSE-SEIS58686.2023.00019
- **F2**：作者：Dananjay Srinivas, Rohan Das, Saeid Tizpaz-Niari, Ashutosh Trivedi, Maria Leonor Pacheco
- **F3**：作者：Sina Gogani-Khiabani, Ashutosh Trivedi, Diptikalyan Saha, Saeid Tizpaz-Niari；ICSE 2026, pp. 272–283
- **F4**：作者：Sina Gogani-Khiabani, Varsha Dewangan, Nina Olson, Ashutosh Trivedi, Saeid Tizpaz-Niari
- **F5**：已正式发表：ESOP 2025（LNCS），pp. 31–61，DOI 10.1007/978-3-031-91121-7_2；作者：Pierre Goutagny, Aymeric Fromherz, Raphaël Monat
- **F7**：完整题目：Metamorphic Testing: A Review of Challenges and Opportunities；年份：论文自印 Publication date: January 2018（Crossref 的 published-print 为 2019）
- **F8**：2014-11 在线发表，刊出于 41(5), 507–525 (2015)
- **G3**：补全：DOI 10.1787/0bb7b24d-en（2013-02）
- **G5**：补全：DOI 10.1787/3afe6ba5-en

## 校验问题

无
