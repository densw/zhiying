create schema if not exists raw;
create schema if not exists analytics;
create schema if not exists ml;
create schema if not exists reporting;

create table if not exists raw.bank_marketing (
  customer_id text primary key,
  age integer,
  job text,
  marital text,
  education text,
  credit_default text,
  balance numeric(12, 2),
  housing text,
  loan text,
  contact text,
  contact_day integer,
  contact_month text,
  duration integer,
  campaign integer,
  pdays integer,
  previous integer,
  poutcome text,
  subscribed text
);

create or replace view analytics.customer_base as
with normalized as (
  select
    customer_id,
    age,
    job,
    marital,
    education,
    credit_default,
    balance,
    housing,
    loan,
    contact,
    contact_day,
    contact_month,
    duration,
    campaign,
    pdays,
    previous,
    poutcome,
    subscribed,
    case when subscribed = 'yes' then 1 else 0 end as converted,
    case contact_month
      when 'jan' then 1
      when 'feb' then 2
      when 'mar' then 3
      when 'apr' then 4
      when 'may' then 5
      when 'jun' then 6
      when 'jul' then 7
      when 'aug' then 8
      when 'sep' then 9
      when 'oct' then 10
      when 'nov' then 11
      when 'dec' then 12
      else 1
    end as month_number,
    case
      when age < 30 then '30岁以下'
      when age between 30 and 39 then '30-39岁'
      when age between 40 and 49 then '40-49岁'
      when age between 50 and 59 then '50-59岁'
      else '60岁及以上'
    end as age_band,
    case
      when balance < 0 then '负余额'
      when balance < 500 then '0-499'
      when balance < 2000 then '500-1,999'
      when balance < 5000 then '2,000-4,999'
      else '5,000以上'
    end as balance_band,
    case
      when previous = 0 then '首次触达'
      when previous between 1 and 2 then '轻度历史触达'
      else '多次历史触达'
    end as previous_band,
    case
      when balance >= 3000 and age between 35 and 60 then '成熟资产型'
      when age < 30 and housing = 'no' then '高潜成长型'
      when job in ('retired', 'management') then '稳健价值型'
      when loan = 'yes' then '信用压力型'
      else '大众经营型'
    end as customer_segment,
    case
      when campaign = 1 then '单次触达'
      when campaign between 2 and 3 then '二至三次'
      when campaign between 4 and 5 then '四至五次'
      else '六次及以上'
    end as campaign_band,
    make_date(2026, case contact_month
      when 'jan' then 1
      when 'feb' then 2
      when 'mar' then 3
      when 'apr' then 4
      when 'may' then 5
      when 'jun' then 6
      when 'jul' then 7
      when 'aug' then 8
      when 'sep' then 9
      when 'oct' then 10
      when 'nov' then 11
      when 'dec' then 12
      else 1
    end, least(greatest(contact_day, 1), 28)) as contact_date
  from raw.bank_marketing
)
select * from normalized;

do $$
begin
  if to_regclass('ml.model_scores') is null then
    execute $table$
      create table ml.model_scores as
      with scored as (
        select
          customer_id,
          round((
            1 / (
              1 + exp(-(
                -2.65
                + case when poutcome = 'success' then 1.70 when poutcome = 'failure' then -0.28 else 0 end
                + case when contact = 'cellular' then 0.42 when contact = 'telephone' then 0.12 else -0.18 end
                + least(greatest(balance, -1000), 10000) / 4200.0
                + case when housing = 'no' then 0.24 else -0.08 end
                + case when loan = 'no' then 0.16 else -0.15 end
                + case when campaign between 1 and 2 then 0.20 when campaign between 3 and 4 then 0.04 else -0.24 end
                + case when previous >= 1 then 0.14 else 0 end
                + case when education = 'tertiary' then 0.12 when education = 'secondary' then 0.05 else 0 end
                + case when contact_month in ('mar', 'apr', 'sep', 'oct', 'dec') then 0.26 else -0.05 end
              ))
            )
          )::numeric, 4) as predicted_probability,
          case
            when contact = 'cellular' or age < 45 then '手机'
            else '电话'
          end as recommended_channel,
          round(((1 / (1 + exp(-(
            -2.65
            + case when poutcome = 'success' then 1.70 when poutcome = 'failure' then -0.28 else 0 end
            + case when contact = 'cellular' then 0.42 when contact = 'telephone' then 0.12 else -0.18 end
            + least(greatest(balance, -1000), 10000) / 4200.0
            + case when housing = 'no' then 0.24 else -0.08 end
            + case when loan = 'no' then 0.16 else -0.15 end
            + case when campaign between 1 and 2 then 0.20 when campaign between 3 and 4 then 0.04 else -0.24 end
            + case when previous >= 1 then 0.14 else 0 end
            + case when education = 'tertiary' then 0.12 when education = 'secondary' then 0.05 else 0 end
            + case when contact_month in ('mar', 'apr', 'sep', 'oct', 'dec') then 0.26 else -0.05 end
          )))) * 780 - 18)::numeric, 2) as expected_value,
          '营销名单优化基线模型'::text as model_name,
          current_timestamp as scored_at
        from analytics.customer_base
      )
      select
        customer_id,
        predicted_probability,
        ntile(10) over (order by predicted_probability desc, customer_id) as score_decile,
        recommended_channel,
        expected_value,
        row_number() over (order by predicted_probability desc, customer_id) as priority_rank,
        model_name,
        scored_at
      from scored
    $table$;
  end if;
end $$;

create or replace view analytics.executive_overview as
select
  count(*) as total_customers,
  sum(converted) as conversions,
  round(avg(converted)::numeric, 4) as conversion_rate,
  round(avg(balance)::numeric, 2) as avg_balance,
  round(avg(campaign)::numeric, 2) as avg_campaign,
  round(avg(case when contact = 'cellular' then 1 else 0 end)::numeric, 4) as mobile_contact_share,
  round(avg(case when previous > 0 then 1 else 0 end)::numeric, 4) as repeat_contact_share
from analytics.customer_base;

create or replace view analytics.monthly_conversion as
select
  month_number,
  to_char(contact_date, 'MM') || '月' as month_label,
  count(*) as contacts,
  sum(converted) as conversions,
  round(avg(converted)::numeric, 4) as conversion_rate
from analytics.customer_base
group by month_number, month_label
order by month_number;

create or replace view analytics.customer_profile as
select
  customer_id,
  customer_segment,
  age_band,
  job,
  marital,
  education,
  balance_band,
  housing,
  loan,
  contact,
  converted
from analytics.customer_base;

create or replace view analytics.customer_segment_performance as
select
  customer_segment,
  count(*) as customer_count,
  sum(converted) as conversions,
  round(avg(converted)::numeric, 4) as conversion_rate,
  round(avg(balance)::numeric, 2) as avg_balance
from analytics.customer_base
group by customer_segment
order by conversion_rate desc, customer_count desc;

create or replace view analytics.channel_performance as
select
  case
    when contact = 'cellular' then '手机'
    when contact = 'telephone' then '电话'
    else '未识别'
  end as channel_name,
  count(*) as contacts,
  sum(converted) as conversions,
  round(avg(converted)::numeric, 4) as conversion_rate,
  round(avg(campaign)::numeric, 2) as avg_attempts,
  round(avg(balance)::numeric, 2) as avg_balance
from analytics.customer_base
group by channel_name
order by conversion_rate desc, contacts desc;

create or replace view analytics.campaign_performance as
select
  campaign_band,
  poutcome as previous_outcome,
  count(*) as contacts,
  sum(converted) as conversions,
  round(avg(converted)::numeric, 4) as conversion_rate,
  round(avg(balance)::numeric, 2) as avg_balance
from analytics.customer_base
group by campaign_band, previous_outcome
order by contacts desc, conversion_rate desc;

create or replace view analytics.model_operations as
select
  s.priority_rank,
  s.score_decile,
  s.predicted_probability,
  s.recommended_channel,
  s.expected_value,
  b.customer_segment,
  b.contact_month,
  b.converted
from ml.model_scores s
join analytics.customer_base b using (customer_id);

create or replace view analytics.model_quality_overview as
with base as (
  select
    score_decile,
    count(*) as customer_count,
    sum(converted) as actual_conversions,
    round(avg(predicted_probability)::numeric, 4) as avg_probability,
    round(avg(converted)::numeric, 4) as actual_rate
  from analytics.model_operations
  group by score_decile
),
overall as (
  select round(avg(converted)::numeric, 4) as base_rate from analytics.customer_base
)
select
  b.score_decile,
  b.customer_count,
  b.actual_conversions,
  b.avg_probability,
  b.actual_rate,
  round((b.actual_rate / nullif(o.base_rate, 0))::numeric, 2) as lift
from base b
cross join overall o
order by b.score_decile desc;

create or replace view analytics.capacity_scenarios as
with capacities(capacity) as (
  values (500), (1000), (2000), (5000), (10000)
),
baseline as (
  select avg(converted)::numeric as base_rate from analytics.customer_base
),
ranked as (
  select
    row_number() over (order by predicted_probability desc, customer_id) as rn,
    predicted_probability,
    expected_value,
    score_decile,
    recommended_channel,
    customer_id,
    converted
  from ml.model_scores
  join analytics.customer_base using (customer_id)
)
select
  c.capacity,
  count(*) as selected_customers,
  round(sum(r.predicted_probability)::numeric, 2) as expected_conversions,
  sum(r.converted) as actual_conversions,
  round(avg(r.predicted_probability)::numeric, 4) as avg_probability,
  round(avg(r.converted)::numeric, 4) as precision,
  round((avg(r.converted) / nullif(b.base_rate, 0))::numeric, 2) as lift,
  round((c.capacity * 18)::numeric, 2) as expected_cost,
  round(sum(r.predicted_probability * 780)::numeric, 2) as expected_revenue,
  round(((sum(r.predicted_probability * 780) - (c.capacity * 18)) / nullif((c.capacity * 18), 0))::numeric, 4) as expected_roi
from capacities c
join baseline b on true
join ranked r on r.rn <= c.capacity
group by c.capacity, b.base_rate
order by c.capacity;

create or replace view analytics.data_quality_overview as
select
  count(*) as total_rows,
  sum(case when job is null or job = '' then 1 else 0 end) as missing_job_rows,
  sum(case when education is null or education = '' then 1 else 0 end) as missing_education_rows,
  sum(case when contact = 'unknown' then 1 else 0 end) as unknown_contact_rows,
  sum(case when duration is not null then 1 else 0 end) as duration_present_rows,
  true as duration_excluded_from_scoring
from analytics.customer_base;

create or replace view analytics.recommendations as
with top_capacity as (
  select * from analytics.capacity_scenarios where capacity = 1000
),
top_decile as (
  select * from analytics.model_quality_overview where score_decile = 10
),
best_channel as (
  select * from analytics.channel_performance order by conversion_rate desc, contacts desc limit 1
),
best_segment as (
  select * from analytics.customer_segment_performance order by conversion_rate desc, customer_count desc limit 1
)
select 1 as priority, '优先保障高分客户的触达容量'::text as recommendation,
  '前 1,000 位客户预计 ROI 显著高于全量均值，应优先保障名单消化能力。'::text as evidence,
  '提升营销投入产出比'::text as expected_impact
from top_capacity
union all
select 2, '优先使用当前最优渠道触达高潜客户',
  '当前渠道表现显示最优渠道具备更高转化率，应在高分名单中优先分配。',
  '提升同等容量下的转化效率'
from best_channel
union all
select 3, '围绕高表现客群设计专门话术',
  '高表现客群转化率持续领先，适合建立专属权益与话术模板。',
  '提升重点客群转化'
from best_segment
union all
select 4, '持续关注顶层分位稳定性',
  '顶层分位 Lift 保持领先，是营销策略的核心信号，应纳入日常监控。',
  '降低名单质量波动风险'
from top_decile;
