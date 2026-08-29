# 数据质量

```sql quality
select *
from analytics.data_quality_overview
```

质量页用于交代本期数据是否完整、是否存在未知渠道过多等问题，以及通话后字段是否已被排除在评分逻辑外。

<BigValue data={quality} value=total_rows title="总记录数" fmt="0,0" />
<BigValue data={quality} value=unknown_contact_rows title="未知渠道记录" fmt="0,0" />
<BigValue data={quality} value=duration_present_rows title="通话后字段存在记录数" fmt="0,0" />

<Table data={quality} title="质量摘要" />
