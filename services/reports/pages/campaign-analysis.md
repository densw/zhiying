# 活动分析

```sql campaigns
select *
from analytics.campaign_performance
order by contacts desc, conversion_rate desc
```

活动页用于回答触达频次和历史结果如何影响本次营销转化，从而帮助团队控制频次、优化名单节奏。

<BarChart
  data={campaigns}
  x=campaign_band
  y=conversion_rate
  series=previous_outcome
  title="不同触达频次的活动表现"
/>

<Table data={campaigns} title="活动经营明细" />
