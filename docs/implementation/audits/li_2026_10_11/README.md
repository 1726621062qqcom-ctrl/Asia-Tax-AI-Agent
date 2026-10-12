# Li 旧发布物核验记录

> 本文为 c8a4cf7 的历史记录。当前 771e452 已补齐旧缺项；当前安装及验收入口见 [合并交接 README](../../../../README_MERGED.md)。

核验日期：2026-10-11。源码：LiZiheng / c8a4cf7a59ef9d8895cd115ce2e4df66850b30e2。

结论：源码与真实数据库已取得；知识库可以打开并通过本次检索抽查；当前发布包不能启动 tax_graph 领域引擎。

- 数据库完整性检查通过；大小 210808832 字节，SHA-256 与 LFS 指针一致。
- 184 条规则定义编译产生 146 条缺引用错误，涉及 37 条规则；去重后缺 74 个参数、8 个法条引用。
- params.csv 与 SQLite 的参数全行一致，clauses.csv 与数据库条款 ID 集合一致。缺项也不在 CSV 中，仅重建数据库无法补齐。
- 新源码引用 D14–D31，但数据库的口径记录只有 D01–D13。
- 可选文档提取器依赖的根目录 信息收集.md 未交付。
- cases/battery 没有已生成 JSON；仓库包含 battery.py 生成器及两份 gold JSON，修齐数据后可生成并验证。不得把空目录的测试结果作为通过。

文件说明：release_audit.json 保存完整机器可读结果，missing_references.csv 列出去重后的缺项及受影响规则，compile_errors.txt 保存编译器的 146 行原始错误，audit_release.py 是复现脚本。

从 B 仓库根目录复现：

```bash
python3 docs/implementation/audits/li_2026_10_11/audit_release.py \
  ../Asia-Tax-AI-Agent-LiZiheng \
  docs/implementation/audits/li_2026_10_11
```

脚本只读源快照并写审计目录。脚本成功结束代表核验记录写出；应检查 compile_passed，而非把脚本退出码当作发布通过。源目录中的实际规则编译可单独复现：

```bash
python3 -m tax_graph.rules
```

该命令在本次快照上失败。首次先修齐发布依赖，再运行 planner/engine 检查；无需反复启动依赖同一失败导入的全部测试。

本次检索只抽查 exact 与 BM25 的四个返回片段及其唯一原文定位，未验证向量模型、完整检索覆盖、法律结论、HTTP、PostgreSQL、前端或真实模型多轮。规则编译失败使实际 planner 端到端验证未能开展。
