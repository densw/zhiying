CREATE SCHEMA IF NOT EXISTS analytics;

CREATE OR REPLACE VIEW analytics.customer_base AS
SELECT
  contact_id,
  customer_code AS customer_id,
  age, job, marital, education, balance, housing, loan, contact,
  day AS contact_day, month, month_number, month_name, campaign, pdays,
  previous, poutcome, subscribed AS converted, age_band, balance_band,
  campaign_intensity AS campaign_band,
  CASE
    WHEN balance >= 3000 AND age BETWEEN 35 AND 60 THEN '成熟资产型'
    WHEN age < 30 AND housing = 'no' THEN '高潜成长型'
    WHEN job IN ('retired', 'management') THEN '稳健价值型'
    WHEN loan = 'yes' THEN '信用压力型'
    ELSE '大众经营型'
  END AS customer_segment
FROM curated.customer_features;

CREATE OR REPLACE VIEW analytics.executive_overview AS
SELECT count(*) AS total_customers, sum(converted) AS conversions,
       round(avg(converted)::numeric, 4) AS conversion_rate,
       round(avg(balance)::numeric, 2) AS avg_balance,
       round(avg(campaign)::numeric, 2) AS avg_campaign
FROM analytics.customer_base;

CREATE OR REPLACE VIEW analytics.monthly_conversion AS
SELECT month_number, month_number::text || '月' AS month_label,
       count(*) AS contacts, sum(converted) AS conversions,
       round(avg(converted)::numeric, 4) AS conversion_rate
FROM analytics.customer_base
GROUP BY month_number ORDER BY month_number;

CREATE OR REPLACE VIEW analytics.customer_profile AS
SELECT customer_id, customer_segment, age_band, job, marital, education,
       balance_band, housing, loan, contact, converted
FROM analytics.customer_base;

CREATE OR REPLACE VIEW analytics.customer_segment_performance AS
SELECT customer_segment, count(*) AS customer_count, sum(converted) AS conversions,
       round(avg(converted)::numeric, 4) AS conversion_rate,
       round(avg(balance)::numeric, 2) AS avg_balance
FROM analytics.customer_base
GROUP BY customer_segment ORDER BY conversion_rate DESC;

CREATE OR REPLACE VIEW analytics.channel_performance AS
SELECT CASE WHEN contact = 'cellular' THEN '手机' WHEN contact = 'telephone' THEN '电话' ELSE '未识别' END AS channel_name,
       count(*) AS contacts, sum(converted) AS conversions,
       round(avg(converted)::numeric, 4) AS conversion_rate,
       round(avg(campaign)::numeric, 2) AS avg_attempts,
       round(avg(balance)::numeric, 2) AS avg_balance
FROM analytics.customer_base GROUP BY channel_name ORDER BY conversion_rate DESC;

CREATE OR REPLACE VIEW analytics.campaign_performance AS
SELECT campaign_band, poutcome AS previous_outcome, count(*) AS contacts,
       sum(converted) AS conversions, round(avg(converted)::numeric, 4) AS conversion_rate,
       round(avg(balance)::numeric, 2) AS avg_balance
FROM analytics.customer_base GROUP BY campaign_band, poutcome ORDER BY contacts DESC;

CREATE OR REPLACE VIEW analytics.model_operations AS
SELECT s.customer_code AS customer_id, s.decile AS score_decile,
       s.propensity_score AS predicted_probability,
       CASE WHEN b.contact = 'cellular' OR b.age < 45 THEN '手机' ELSE '电话' END AS recommended_channel,
       round((s.propensity_score * 680 - 18)::numeric, 2) AS expected_value,
       row_number() OVER (ORDER BY s.propensity_score DESC) AS priority_rank,
       b.customer_segment, b.month_name AS contact_month, b.converted
FROM ml.model_scores s
JOIN analytics.customer_base b ON b.contact_id = s.contact_id
WHERE s.run_id = (SELECT run_id FROM ml.training_runs WHERE selected_model = TRUE ORDER BY trained_at DESC LIMIT 1);

CREATE OR REPLACE VIEW analytics.model_quality_overview AS
SELECT d.decile AS score_decile, d.prospects AS customer_count,
       d.subscribers AS actual_conversions, round(d.average_score::numeric, 4) AS avg_probability,
       round(d.response_rate::numeric, 4) AS actual_rate,
       round(d.lift::numeric, 2) AS lift
FROM ml.model_score_deciles d
WHERE d.run_id = (SELECT run_id FROM ml.training_runs WHERE selected_model = TRUE ORDER BY trained_at DESC LIMIT 1)
ORDER BY d.decile;

CREATE OR REPLACE VIEW analytics.capacity_scenarios AS
WITH capacities(capacity) AS (VALUES (500), (1000), (2000), (5000), (10000)),
latest AS (SELECT run_id FROM ml.training_runs WHERE selected_model = TRUE ORDER BY trained_at DESC LIMIT 1),
ranked AS (
  SELECT s.*, row_number() OVER (ORDER BY propensity_score DESC) AS rn
  FROM ml.model_scores s JOIN latest USING (run_id)
), baseline AS (SELECT avg(actual_subscribed)::numeric AS base_rate FROM ranked)
SELECT c.capacity, count(r.*) AS selected_customers,
       round(sum(r.propensity_score)::numeric, 2) AS expected_conversions,
       sum(r.actual_subscribed) AS actual_conversions,
       round(avg(r.propensity_score)::numeric, 4) AS avg_probability,
       round(avg(r.actual_subscribed)::numeric, 4) AS precision,
       round((avg(r.actual_subscribed) / nullif(b.base_rate, 0))::numeric, 2) AS lift,
       round((c.capacity * 18)::numeric, 2) AS expected_cost,
       round((sum(r.propensity_score) * 680)::numeric, 2) AS expected_revenue,
       round((((sum(r.propensity_score) * 680) - (c.capacity * 18)) / nullif((c.capacity * 18), 0))::numeric, 4) AS expected_roi
FROM capacities c CROSS JOIN baseline b JOIN ranked r ON r.rn <= c.capacity
GROUP BY c.capacity, b.base_rate ORDER BY c.capacity;

CREATE OR REPLACE VIEW analytics.data_quality_overview AS
SELECT count(*) AS total_rows,
       sum(CASE WHEN job IS NULL OR job = '' THEN 1 ELSE 0 END) AS missing_job_rows,
       sum(CASE WHEN education IS NULL OR education = '' THEN 1 ELSE 0 END) AS missing_education_rows,
       sum(CASE WHEN contact = 'unknown' THEN 1 ELSE 0 END) AS unknown_contact_rows,
       true AS duration_excluded_from_scoring
FROM analytics.customer_base;

CREATE OR REPLACE VIEW analytics.recommendations AS
SELECT 1 AS priority, '优先保障高分客户的触达容量'::text AS recommendation,
       '前 1,000 位客户的策略增益高于随机触达，应优先保障名单消化能力。'::text AS evidence,
       '提升营销投入产出比'::text AS expected_impact
UNION ALL SELECT 2, '优先采用历史表现更好的联系渠道', '渠道转化表现存在显著差异，应结合高分名单分配触达渠道。', '提升同等容量下的转化效率'
UNION ALL SELECT 3, '持续监控顶层评分分位', '顶层分位是营销名单质量的核心信号，应每日检查稳定性。', '降低名单质量波动风险';
