with staged as (
    select * from {{ref('stg_fannie_mae_loan_performance')}}
),
one_row_per_loan as (
    select
        loan_identifier,
        channel,
        original_upb,
        current_actual_upb as current_upb,
        original_loan_to_value_ratio_ltv as ltv,
        borrower_credit_score_at_origination as credit_score,
        vintages_quarter,
        first_payment_date,
        maturity_date,
        monthly_reporting_period as first_reported_month
    from (
        select s.*,
        row_number() over (
            partition by loan_identifier order by monthly_reporting_period asc
            ) as rn
        from staged s
        ) t
    where rn = 1
)
select * from one_row_per_loan