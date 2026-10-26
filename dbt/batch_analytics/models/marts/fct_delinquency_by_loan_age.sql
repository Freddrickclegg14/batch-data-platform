-- Controls for loan seasoning: delinquency rate by LOAN AGE (months
-- since origination) instead of calendar month. If 2008Q1 and 2024Q1
-- show similar delinquency-by-age curves, the earlier finding (rate
-- rising regardless of market direction) really is just seasoning. If
-- 2008Q1's curve rises meaningfully FASTER than 2024Q1's at the same
-- age, that's a real vintage/crisis effect the calendar-month version
-- couldn't isolate.


with monthly_performance as (
    select *
    from {{ref('fct_loan_monthly_performance')}}
),
classified as (
    select
        vintage_quarter,
        loan_age,
        loan_identifier,
        case
            when current_loan_delinquency_status = 'XX' then null
            when safe_cast(current_loan_delinquency_status as int64) >= 3 then true
            when safe_cast(current_loan_delinquency_status as int64) < 3 then false
            else null
        end as is_delinquent
    from monthly_performance
    where loan_age >= 0 
),
aggregated as (
    select 
        vintage_quarter,
        loan_age,
        count(*) as total_loan_reported,
        countif(is_delinquent is not null) as loans_with_known_status,
        countif(is_delinquent) as delinquent_loans,
        safe_divide(
            countif(is_delinquent),
            countif(is_delinquent is not null)
        ) as delinquency_rate
    from classified 
    group by vintage_quarter, loan_age  
)

select * from aggregated
order by vintage_quarter, loan_age