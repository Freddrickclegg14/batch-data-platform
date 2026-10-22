with source as (
    select * from {{source('staging_bq','yfinance_prices')}}
),
cleaned as (
    select 
        ticker,
        date,
        open,
        low,
        high,
        close,
        adj_close,
        volume
    from source
)
select * from cleaned
-- after historical re-ingests (e.g., correlation analysis). The loader has
-- a safety net, but staging enforces uniqueness for downstream tests.
qualify row_number() over (
    partition by ticker, date 
    order by close desc
) = 1
