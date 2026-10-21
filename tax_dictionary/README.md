# Country Tax Dictionary：分类与资料层

本目录把现有资料整理为按**法域、税种、主体、所得类型、文件类型、时间和证据状态**浏览的税务词典。当前提供静态 Markdown、CSV 和 JSON，没有新增交互前端，也不新增或修改税额计算规则。

## 从哪里看

| 内容 | 入口 |
|---|---|
| 三地税务差异总览 | [COMPARISON.md](COMPARISON.md) |
| 中国内地词典 | [countries/CN.md](countries/CN.md) |
| 香港词典 | [countries/HK.md](countries/HK.md) |
| 新加坡词典 | [countries/SG.md](countries/SG.md) |
| 全量资料的业务分类与原文链接 | [SOURCES.md](SOURCES.md) |
| 覆盖缺口、未分类资料和证据待补项 | [GAPS.md](GAPS.md) |
| 数据结构、字段含义及后续扩展 | [SCHEMA.md](SCHEMA.md) |
| 实际数量与输入指纹 | [data/inventory.json](data/inventory.json) |

词典和比较表使用英文名称，原文引语保留原语言，便于后续接入英文产品。

## 分几层存放

```text
official/                           官方资料层：原件、条款、参数、来源、时效
  official.sqlite                   已有 SQLite，不是本次才引入
  manifest.csv / params.csv          已有登记与参数

tax_dictionary/                     业务整理层：独立于官方原文
  taxonomy.json                     可维护的分类与状态词表
  profiles.json                     三地各主题的说明、边界和展示参数
  build.py                          只读原库，验证引用并生成下列产物
  data/                             可供后续前端或接口使用的数据
  countries/                        每地词典卡片
  COMPARISON.md                      同主题横向比较
  SOURCES.md / GAPS.md               分类索引、缺口与质量待办
```

保持原资料路径与引用编号，给资料增加关联索引；不通过移动 PDF 或复制法规文本来重新分类。这里的业务说明是编辑整理内容，不冒充 `official/` 中的官方原文。

## 怎样分类

- **法域**：CN、HK、SG；双边材料可关联两个法域，国际材料单独保留来源归属。
- **主题**：23 类，包含协定、企业所得税、个人所得税、继承/遗产/赠与税、迁出税、CFC、预提税、抵免、股权损益、重组、常设机构、转让定价、反滥用、IP、间接税、印花税、不动产税、附加、关税、支柱二、亏损、程序、公司法。
- **主体**：公司与个人、合伙、信托分开；当前计算能力主要服务公司场景。
- **所得/交易类型**：沿用参数与规则中的 `income`，不把“税种”和“交易类型”混为同一字段。
- **文献形式**：法律、法规、协定、议定书、指引、表单、判决、裁定等沿用原登记；语言、分片、拼装件、别名和作品编号分别保留。
- **时间**：分别保留签署/发布、原库登记的生效区间、检索日期和效力标记。缺失日期明确为空，不自动当作一直有效。

分类依据也单独记录：参数引用、规则引用、先例问题、文件标识、标题关键词和父文件上下文。`reference_linked` 表示可以沿引用回查；`metadata_inferred` 表示目录推断，尚需业务复核；`needs_review` 不会被强塞进一个税种。

## 覆盖状态独立呈现

| 维度 | 表示什么 | 不代表什么 |
|---|---|---|
| `source_status` | 是否索引到相关资料，或仅整部法规附带收录 | 该税种已经完整收录 |
| `structure_status` | 是否关联到结构化参数 | 所有条款已经可计算 |
| `model_status` | 是否存在对应的已编译规则 | 适用于所有纳税人及所有事实组合 |
| `judgement_status` | 关联规则中是否有裁量或事实认定 | 已经获得对当前案例的认可 |
| `completeness_status` | 当前分类是否仅为部分覆盖 | 全球资料已穷尽收录 |

**空白项不等于零税负。**遗产税与迁出税保留为独立待补类别；股权出售、重组、公司迁册不会被自动等同于迁出税。港新有限的航空/航运协定不会被显示为一般所得全面协定。

## 构建与检查

在项目根目录执行：

```powershell
& 'C:\Coding\Anaconda\envs\pytorch\python.exe' -m tax_dictionary.build --as-of 2026-10-16
& 'C:\Coding\Anaconda\envs\pytorch\python.exe' -m tax_dictionary.check
& 'C:\Coding\Anaconda\envs\pytorch\python.exe' -m tax_dictionary.build --as-of 2026-10-16 --check
```

`--as-of` 是**目录整理日期**，不是“已重新联网核实当日所有税法”的证明。构建不联网、不读取私有案例、不调用 LLM、不改变原库、不重建向量。

原库更新后先按原有流程重建 `official.sqlite`，再构建词典。若 SQLite 与 CSV 不一致，词典构建会停止，避免拼出不同版本的数据。词典依赖的参数引语逐字核对；无引语和无直接来源的记录单独列入 `GAPS.md`。

## 怎样渐进扩展

1. 在原资料库收录可追溯的官方材料，维护生效、取代及来源信息。
2. 维护 `taxonomy.json` 和 `profiles.json`，给新法域或税种增加稳定标识及边界说明。
3. 增补结构化参数和必要的计算规则；收录与可计算状态分别变化。
4. 重新生成并检查词典，处理未分类与证据缺口。

增加法域时还需要扩展构建器的法域识别与规则映射；新增一个国家名称本身不会赋予该国计算能力。后续前端可以直接消费 `data/dictionary.json`、`data/coverage.csv` 和 `data/treaties.json`。
