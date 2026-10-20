--Working on formula

{% set lag_months = var('delinquency_lag_months', 3) %}
 
with market_daily as (
    select *
    from {{ ref('stg_yfinance_prices') }}
    where ticker = '^GSPC'
),
 
market_monthly as (
    select
        date_trunc(date, month) as month,
        -- last trading day's close for that month
        array_agg(close order by date desc limit 1)[offset(0)] as month_end_close
    from market_daily
    group by month
),
 
market_with_return as (
    select
        month,
        month_end_close,
        safe_divide(
            month_end_close - lag(month_end_close) over (order by month),
            lag(month_end_close) over (order by month)
        ) as pct_change_mom
    from market_monthly
),
 
delinquency_monthly as (
    -- Aggregated across both vintages. Split by vintage_quarter instead
    -- if you want to see 2008Q1 vs 2024Q1 react differently.
    select
        monthly_reporting_period,
        safe_divide(
            sum(delinquent_loans),
            sum(loans_with_known_status)
        ) as avg_delinquency_rate
    from {{ ref('fct_delinquency_by_vintage') }}
    group by monthly_reporting_period
),
 
joined as (
    select
        m.month as market_month,
        m.month_end_close,
        m.pct_change_mom as market_pct_change_mom,
        date_add(m.month, interval {{ lag_months }} month) as delinquency_month,
        d.avg_delinquency_rate
    from market_with_return m
    left join delinquency_monthly d
        on date_add(m.month, interval {{ lag_months }} month) = d.monthly_reporting_period
)
 
select * from joined
order by market_month