# 渠道分析

```sql channels
select *
from analytics.channel_performance
order by conversion_rate desc, contacts desc
```

渠道页聚焦同等容量下哪种触达方式更值得优先配置，便于把高分客户和最优触达方式一起下发给执行团队。

<BarChart
  data={channels}
  x=channel_name
  y=conversion_rate
  title="渠道转化效率"
/>

<Table data={channels} title="渠道经营明细" />
