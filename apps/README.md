# Applications

本目录包含本地香港 FSIE 聊天研究 Demo 与 FastAPI 服务。

`api/main.py` 提供本地会话、对话与健康接口，`api/static/` 提供中文聊天页。运行 `make demo` 后打开 http://127.0.0.1:8000 。默认不调用模型、不依赖数据库；仅作受控 L0 研究演示。详见 `docs/implementation/CHAT_DEMO_RUNBOOK.md`。
