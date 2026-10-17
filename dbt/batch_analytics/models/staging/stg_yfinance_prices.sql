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
