# 客户分析

```sql customer_segments
select *
from analytics.customer_segment_performance
order by conversion_rate desc, customer_count desc
```

```sql customer_profile
select customer_segment, age_band, job, education, balance_band, converted
from analytics.customer_profile
limit 100
```

从客户结构看，平台已经把原始客户统一归并为便于业务理解的中文客群，并保留年龄、职业、教育与余额层级，方便团队进一步拆解高价值人群。

<BarChart
  data={customer_segments}
  x=customer_segment
  y=conversion_rate
  title="客群转化率"
/>

<Table data={customer_segments} title="客群经营表现" />

<Table data={customer_profile} title="客户结构样本" />
