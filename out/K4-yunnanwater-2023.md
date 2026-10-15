# 问题单：K4-yunnanwater-2023（模板 holding）

方案尚不能给出：下列数据或确认会改变所选方案或其保证税额。只需答这些；答不上请填 unknown（按最不利处理，不会补值）。
答复写进 `<案例名>.answers.json`：data（数值或 {"value", "source"}）、actions（yes / no / unknown）、rulings（yes / no / unknown）、library。

## CN∩HK∩BVI

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 必答（缺则税额无界） | `flow:unwind.amount` | 请提供：现有 HOLD 所持 OP 股权在转出日的市场价值（撤销或迁出 HOLD 时按此转给 ULT 或新公司）（flow:unwind.amount） | 金额 | 评估报告；表单：cn.sta.2019-35.a01 · 14.享受协定待遇所得金额；cn.sta.2019-16.a08 · 合同总金额；cn.sta.2019-16.a08 · 本次申报收入 人民币金额 | 无界 |
| 必答（缺则税额无界） | `flow:wind.amount` | 请提供：现有 HOLD 清算时分配给股东 ULT 的全部剩余财产（含 OP 股权或其转让价款，扣除税费与负债后）（flow:wind.amount） | 金额 | 清算方案与资产负债表；表单：cn.sta.2019-35.a01 · 14.享受协定待遇所得金额；cn.sta.2019-16.a08 · 合同总金额；cn.sta.2019-16.a08 · 本次申报收入 人民币金额 | 无界 |

候选结构 7 个；其中需要上面必答数据才能计算的 7 个。
