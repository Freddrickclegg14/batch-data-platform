with source as (
    select * from {{source('staging_bq','fannie_mae_loan_performance')}}
),

cleaned AS (   
    select 
        loan_identifier,
        monthly_reporting_period,
        vintages_quarter as vintage_quarter,
        channel,
        seller_name,
        servicer_name,
        original_interest_rate,
        current_interest_rate,
        original_upb,
        current_actual_upb,
        original_loan_term,
        origination_date,
        first_payment_date,
        loan_age,
        maturity_date,
        original_loan_to_value_ratio_ltv,
        original_combined_loan_to_value_ratio_cltv,
        debt_to_income_dti,
        borrower_credit_score_at_origination,
        occupancy_status,
        property_state,
        current_loan_delinquency_status,
        zero_balance_code,
        zero_balance_effective_date,
        data_quality_flag 
    from source
    where data_quality_flag is null
)
select * from cleaned