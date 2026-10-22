with monthly_performance as (
    select *
    from {{ ref('fct_loan_monthly_performance') }}
),
 
classified as (
    select
        vintage_quarter,
        monthly_reporting_period,
        loan_identifier,
        case
            when current_loan_delinquency_status = 'XX' then null
            when safe_cast(current_loan_delinquency_status as int64) >= 3 then true
            when safe_cast(current_loan_delinquency_status as int64) < 3 then false
            else null
        end as is_seriously_delinquent
    from monthly_performance
),
 
aggregated as (
    select
        vintage_quarter,
        monthly_reporting_period,
        count(*) as total_loans_reported,
        countif(is_seriously_delinquent is not null) as loans_with_known_status,
        countif(is_seriously_delinquent) as delinquent_loans,
        safe_divide(
            countif(is_seriously_delinquent),
            countif(is_seriously_delinquent is not null)
        ) as delinquency_rate
    from classified
    group by vintage_quarter, monthly_reporting_period
)
 
select * from aggregated
order by vintage_quarter, monthly_reporting_period
 