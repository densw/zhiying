# 自动经营报告

该目录提供一套真实运行的中文报告站点：

- 使用官方 Evidence 镜像构建与运行
- 直接连接 PostgreSQL 中的 `analytics` / `ml` 视图
- 输出经营摘要、客户、渠道、活动、模型、决策、质量、建议等多页面报告

## 启动

```powershell
docker compose -f services/reports/docker-compose.reports.yml up --build
```

默认端口：

- PostgreSQL: `55433`
- 报告站点: `3010`

## 说明

- 启动时会复用 `services/analytics` 中的落库与视图脚本，以保证与经营分析中心使用同一批真实数据口径
