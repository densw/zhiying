# 经营摘要

```sql overview_kpis
select
  total_customers,
  conversions,
  round(conversion_rate * 100, 2) as conversion_rate_pct,
  avg_balance,
  avg_campaign
from analytics.executive_overview
```

```sql monthly_trend
select month_label, conversion_rate
from analytics.monthly_conversion
order by month_number
```

```sql top_capacity
select *
from analytics.capacity_scenarios
where capacity = 1000
```

```sql top_recommendations
select *
from analytics.recommendations
order by priority
```

# 本期发生了什么

<BigValue data={overview_kpis} value=total_customers title="可经营客户记录" fmt="0,0" />
<BigValue data={overview_kpis} value=conversions title="成功认购" fmt="0,0" />
<BigValue data={overview_kpis} value=conversion_rate_pct title="整体转化率" fmt="0.00" suffix="%" />
<BigValue data={overview_kpis} value=avg_balance title="平均余额" fmt="0,0.00" />

模型优先策略下，前 1,000 位客户对应的预计转化、预计收益与 ROI 已经在数据库中实时汇总，可直接为每日营销安排提供依据。

<LineChart
  data={monthly_trend}
  x=month_label
  y=conversion_rate
  title="月度转化走势"
/>

<Table data={top_capacity} title="容量为 1,000 时的推荐策略结果" />

<Table data={top_recommendations} title="自动经营建议" />
