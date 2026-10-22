with staged as (
    select *
    from {{ ref('stg_fannie_mae_loan_performance') }}
),
 
monthly as (
    select
        loan_identifier,
        monthly_reporting_period,
        vintage_quarter,
        current_interest_rate,
        current_actual_upb,
        loan_age,
        current_loan_delinquency_status,
        zero_balance_code,
        zero_balance_effective_date
    from staged
)
 
select * from monthly