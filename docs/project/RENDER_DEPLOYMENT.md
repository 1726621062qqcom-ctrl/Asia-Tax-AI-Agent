# Taxrora 云端部署

网站：https://taxrora.onrender.com

## 团队更新流程

1. 拉取最新 main，在自己的功能分支开发和测试。
2. 推送功能分支，通过 PR 合并到 main。
3. Render 监听 main 的提交，自动构建并部署；在服务 Deploys 页面检查结果。
4. 部署成功后检查网站。构建失败时查看日志并修复，不代表新版本已上线。

Render 服务名为 taxrora，使用 Free 方案，自动部署设置为 On Commit。
构建命令：`bash scripts/render_build.sh`。
启动命令：`uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT --workers 1`。
健康检查：`/health`。

## 配置与边界

密钥和数据库连接在 Render Environment 中维护；不要提交 .env。
当前发布包含 React 界面和现有聊天服务。完整 Li 结构计算组件尚未接通云端；自动部署配置不代表该功能已经完成。
历史 deploy/taxrora-current-ui 和 deploy/taxrora-free-demo 分支不再是线上发布来源。

## 回滚

在 Render 的部署历史选择已验证版本回滚。回滚后检查自动部署开关；必要时先暂停自动部署，再在 main 上通过 revert 修复，验证后恢复 On Commit。
