CREATE OR REPLACE TABLE stg_awards AS
SELECT
    ocid,
    award_id,
    CAST(award_date AS DATE) AS award_date,
    COALESCE(buyer_id, buyer_name) AS buyer_key,
    buyer_name,
    COALESCE(supplier_id, supplier_name) AS supplier_key,
    supplier_name,
    category_code,
    category_name,
    CAST(award_value AS DECIMAL(18,2)) AS award_value,
    currency,
    title
FROM awards_input;

CREATE OR REPLACE TABLE dim_buyer AS
SELECT row_number() OVER (ORDER BY buyer_key) AS buyer_sk, buyer_key, buyer_name
FROM (SELECT DISTINCT buyer_key, buyer_name FROM stg_awards);

CREATE OR REPLACE TABLE dim_supplier AS
SELECT row_number() OVER (ORDER BY supplier_key) AS supplier_sk, supplier_key, supplier_name
FROM (SELECT DISTINCT supplier_key, supplier_name FROM stg_awards);

CREATE OR REPLACE TABLE dim_category AS
SELECT row_number() OVER (ORDER BY category_code) AS category_sk, category_code, category_name
FROM (SELECT DISTINCT category_code, category_name FROM stg_awards);

CREATE OR REPLACE TABLE dim_date AS
SELECT DISTINCT award_date AS date_key,
       year(award_date) AS calendar_year,
       month(award_date) AS calendar_month,
       CASE WHEN month(award_date) >= 4 THEN year(award_date) ELSE year(award_date) - 1 END AS fiscal_year_start
FROM stg_awards WHERE award_date IS NOT NULL;

CREATE OR REPLACE TABLE dim_inflation AS
SELECT CAST(month AS DATE) AS month, CAST(cpih_index AS DECIMAL(10,3)) AS cpih_index
FROM inflation_input;

CREATE OR REPLACE TABLE fact_award AS
SELECT
    s.ocid, s.award_id, s.award_date, b.buyer_sk, p.supplier_sk, c.category_sk,
    s.award_value, s.currency, s.title,
    CASE WHEN s.award_value >
        avg(s.award_value) OVER (PARTITION BY c.category_sk) +
        2 * stddev_pop(s.award_value) OVER (PARTITION BY c.category_sk)
    THEN 1 ELSE 0 END AS value_anomaly_flag
FROM stg_awards s
JOIN dim_buyer b USING (buyer_key, buyer_name)
JOIN dim_supplier p USING (supplier_key, supplier_name)
JOIN dim_category c USING (category_code, category_name);

CREATE OR REPLACE VIEW mart_supplier_risk AS
WITH supplier_stats AS (
    SELECT supplier_sk, sum(award_value) AS total_value, count(*) AS award_count,
           avg(value_anomaly_flag) AS anomaly_rate
    FROM fact_award GROUP BY supplier_sk
), buyer_dependency AS (
    SELECT supplier_sk, max(buyer_value) / sum(buyer_value) AS dependency_ratio
    FROM (SELECT supplier_sk, buyer_sk, sum(award_value) AS buyer_value
          FROM fact_award GROUP BY supplier_sk, buyer_sk)
    GROUP BY supplier_sk
), market AS (
    SELECT sum(total_value) AS market_value FROM supplier_stats
)
SELECT d.supplier_name, s.total_value, s.award_count,
       round(100 * s.total_value / m.market_value, 2) AS market_share_pct,
       round(b.dependency_ratio, 3) AS dependency_ratio,
       round(s.anomaly_rate, 3) AS anomaly_rate,
       round(100 * (0.45 * b.dependency_ratio + 0.30 * s.anomaly_rate +
             0.25 * least(s.total_value / m.market_value * 5, 1)), 1) AS risk_score
FROM supplier_stats s JOIN dim_supplier d USING (supplier_sk)
JOIN buyer_dependency b USING (supplier_sk) CROSS JOIN market m;

CREATE OR REPLACE VIEW mart_monthly_spend AS
WITH monthly AS (
    SELECT date_trunc('month', award_date)::DATE AS award_month,
           count(*) AS award_count, sum(award_value) AS awarded_value
    FROM fact_award GROUP BY 1
), latest_index AS (SELECT max(cpih_index) AS cpih_index FROM dim_inflation)
SELECT m.*, i.cpih_index,
       round(m.awarded_value * l.cpih_index / i.cpih_index, 2) AS real_awarded_value_latest_prices
FROM monthly m JOIN dim_inflation i ON m.award_month = i.month
CROSS JOIN latest_index l ORDER BY m.award_month;

CREATE OR REPLACE VIEW quality_failures AS
SELECT * FROM stg_awards
WHERE award_id IS NULL OR buyer_name IS NULL OR supplier_name IS NULL
   OR award_value IS NULL OR award_value < 0;
