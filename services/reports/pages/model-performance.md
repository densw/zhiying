# 模型表现

```sql quality
select *
from analytics.model_quality_overview
order by score_decile desc
```

```sql capacity
select *
from analytics.capacity_scenarios
order by capacity
```

模型页不是展示抽象算法，而是直接关注高分客户分位、转化差异与不同营销容量下的收益变化。

<BarChart
  data={quality}
  x=score_decile
  y=lift
  title="分位增益表现"
/>

<Table data={quality} title="分位质量明细" />

<Table data={capacity} title="容量策略模拟" />
