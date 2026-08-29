# 决策分析

```sql decisions
select
  capacity,
  selected_customers,
  expected_conversions,
  avg_probability,
  precision,
  lift,
  expected_cost,
  expected_revenue,
  expected_roi
from analytics.capacity_scenarios
order by capacity
```

决策页回答“应该联系多少客户”这一最核心问题，把高分名单转成容量、成本、收益与 ROI 的业务语言。

<LineChart
  data={decisions}
  x=capacity
  y=expected_roi
  title="不同容量下的预计 ROI"
/>

<Table data={decisions} title="营销容量决策表" />
