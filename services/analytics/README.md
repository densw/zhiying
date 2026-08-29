# 经营分析中心

该目录提供一套可独立启动的真实经营分析服务：

- 使用 PostgreSQL 载入 `bank-full.csv`
- 生成中文经营分析视图与模型运营视图
- 使用官方 Superset 镜像自动创建数据库连接、数据集、图表与 5 套中文看板

本目录不暴露源仓库地址，也不在用户可见文案中出现外链。

## 启动

```powershell
docker compose -f services/analytics/docker-compose.analytics.yml up --build
```

默认端口：

- PostgreSQL: `55432`
- 经营分析中心: `8090`

## 账号

- 用户名: `admin`
- 密码: `admin123`

## 说明

- 初始化脚本会在容器启动时把真实 CSV 装载进 `raw.bank_marketing`
- 如果数据库中还不存在 `ml.model_scores`，脚本会基于允许训练字段生成一份可复现实验评分表，供分析与报告复用
