# Infrastructure

Taxrora 使用 Render 免费 Web Service，优先申请 `taxrora.onrender.com`，实际地址以平台分配为准。无需旧域名、Cloudflare Tunnel 或本地常开电脑。当前配置已准备，线上状态须以部署验收为准。

## Render 免费部署

根目录 `render.yaml` 声明唯一的 Python Web Service，明确设置 `plan: free`，不创建数据库或磁盘，不启用模型。Render 直接构建 Python 应用，无需本机 Docker。

1. 将已验证的代码推送到 GitHub `deploy/taxrora-free-demo`。远程 `main` 已包含比本地 Demo 更新的完整应用，不要用 Demo 覆盖它。
2. 登录 Render，创建 Blueprint 并选择本仓库；核对只有一个 Free Web Service，再部署。也可手动创建 Web Service，照 `render.yaml` 填写配置。
3. 如果名称被占用，选择 `taxrora-app` 等可用名称。平台注入的 `RENDER_EXTERNAL_HOSTNAME` 自动加入准确的主机白名单；不要使用通配符。
4. 使用平台 HTTPS 地址验收首页、健康检查、新建对话、回答引用、更正和清空。`FSIE_SECURE_COOKIES=true` 确保代理终止 TLS 时 Cookie 仍标记 Secure。

平台的免费服务有休眠和用量限制：闲置 15 分钟休眠，下次访问自动唤醒，通常约一分钟。会话仅在内存里，休眠、重启、部署都会清空。无需定时请求强行保活。关闭自动部署，后续更新手动触发以控制构建用量。

保持零预算：核对工作区没有付费资源和附加服务；不要添加付款方式，或在已有付款方式的账户中先核对超额计费与支出限制。免费实例不等于所有超额用量免费。模型开关保持关闭，不配置模型密钥。

这是公开的一般问题/虚构案例研究演示，没有用户账户和真实案件持久化。原有规则引擎仍是 CLI 流程，没有因部署而接入聊天。

官方说明：https://render.com/docs/free 、https://render.com/docs/deploy-fastapi 。

## 聊天演示容器

在仓库根目录构建和运行：

```sh
docker build -t taxrora .
docker run --rm -p 127.0.0.1:8000:8000 \
  -e 'FSIE_ALLOWED_HOSTS=["localhost","127.0.0.1","taxrora.onrender.com"]' \
  taxrora
```

容器使用非 root 用户，监听 8000，健康检查为 `/health`。构建上下文只允许应用代码和聊天公开语料，不包含 `.env`、Git 历史、原始资料或本地数据库。默认关闭模型，不需要 PostgreSQL。

云端必须使用单实例、单 worker：会话保存在进程内，重启会丢失，扩容前需要外部会话存储。HTTPS 由云平台或可信反向代理终止；应仅信任实际代理地址的转发头，以便正确设置 Secure Cookie。不要无条件信任公网客户端的转发头。

自定义域名通过 `FSIE_ALLOWED_HOSTS` JSON 列表配置；现有会话 Cookie 不代表用户身份认证。启用真实案件或收费模型前需另行实现访问控制与限流。模型配置通过云平台 secret 管理，启用前确认调用预算和访问边界。

上线验收：通过目标 HTTPS 地址检查首页品牌、`/health`、`/api/config`、新建对话、带引用回答、事实更正和清空会话。必须验证 HTTPS Cookie 带 Secure 属性。确认网站在本地服务关闭时仍可访问，才算完成云托管验收；本机 Tunnel 不作为常驻云托管。

## 原有数据库链路

`postgres/` 保留本地 PostgreSQL 配置。聊天容器不执行数据库迁移，也不对外提供原有 CLI 分析与报告流程。后续启用云数据库时另行配置备份、身份与数据保留。
