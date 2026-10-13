# import pytest

FILE_COLUMNS = [
    "reference_pool_id",  # position 1: Reference Pool ID (always blank for SF files)
    "loan_identifier",  # position 2: Loan Identifier
    "monthly_reporting_period",  # position 3: Monthly Reporting Period
    "channel",  # position 4: Channel
    "seller_name",  # position 5: Seller Name
    "servicer_name",  # position 6: Servicer Name
    "master_servicer",  # position 7: Master Servicer
    "original_interest_rate",  # position 8: Original Interest Rate
    "current_interest_rate",  # position 9: Current Interest Rate
    "original_upb",  # position 10: Original UPB
    "upb_at_issuance",  # position 11: UPB at Issuance
    "current_actual_upb",  # position 12: Current Actual UPB
    "original_loan_term",  # position 13: Original Loan Term
    "origination_date",  # position 14: Origination Date
    "first_payment_date",  # position 15: First Payment Date
    "loan_age",  # position 16: Loan Age
    "remaining_months_to_legal_maturity",  # position 17: Remaining Months to Legal Maturity
    "remaining_months_to_maturity",  # position 18: Remaining Months To Maturity
    "maturity_date",  # position 19: Maturity Date
    "original_loan_to_value_ratio_ltv",  # position 20: Original Loan to Value Ratio (LTV)
    "original_combined_loan_to_value_ratio_cltv",  # position 21: Original Combined Loan to Value Ratio (CLTV)
    "number_of_borrowers",  # position 22: Number of Borrowers
    "debt_to_income_dti",  # position 23: Debt-To-Income (DTI)
    "borrower_credit_score_at_origination",  # position 24: Borrower Credit Score at Origination
    "co_borrower_credit_score_at_origination",  # position 25: Co-Borrower Credit Score at Origination
    "first_time_home_buyer_indicator",  # position 26: First Time Home Buyer Indicator
    "loan_purpose",  # position 27: Loan Purpose
    "property_type",  # position 28: Property Type
    "number_of_units",  # position 29: Number of Units
    "occupancy_status",  # position 30: Occupancy Status
    "property_state",  # position 31: Property State
    "metropolitan_statistical_area_msa_or_metropolitan_statistical_division_area_msda",  # position 32: Metropolitan Statistical Area (MSA) or Metropolitan Statistical Division Area (MSDA)
    "zip_code_short",  # position 33: Zip Code Short
    "mortgage_insurance_percentage",  # position 34: Mortgage Insurance Percentage
    "amortization_type",  # position 35: Amortization Type
    "prepayment_penalty_indicator",  # position 36: Prepayment Penalty Indicator
    "interest_only_loan_indicator",  # position 37: Interest Only Loan Indicator
    "interest_only_first_principal_and_interest_payment_date",  # position 38: Interest Only First Principal And Interest Payment Date
    "months_to_amortization",  # position 39: Months to Amortization
    "current_loan_delinquency_status",  # position 40: Current Loan Delinquency Status
    "loan_payment_history",  # position 41: Loan Payment History
    "modification_flag",  # position 42: Modification Flag
    "mortgage_insurance_cancellation_indicator",  # position 43: Mortgage Insurance Cancellation Indicator
    "zero_balance_code",  # position 44: Zero Balance Code
    "zero_balance_effective_date",  # position 45: Zero Balance Effective Date
    "upb_at_the_time_of_removal",  # position 46: UPB at the Time of Removal
    "repurchase_date",  # position 47: Repurchase Date
    "scheduled_principal_current",  # position 48: Scheduled Principal Current
    "total_principal_current",  # position 49: Total Principal Current
    "unscheduled_principal_current",  # position 50: Unscheduled Principal Current
    "last_paid_installment_date",  # position 51: Last Paid Installment Date
    "foreclosure_date",  # position 52: Foreclosure Date
    "disposition_date",  # position 53: Disposition Date
    "foreclosure_costs",  # position 54: Foreclosure Costs
    "property_preservation_and_repair_costs",  # position 55: Property Preservation and Repair Costs
    "asset_recovery_costs",  # position 56: Asset Recovery Costs
    "miscellaneous_holding_expenses_and_credits",  # position 57: Miscellaneous Holding Expenses and Credits
    "associated_taxes_for_holding_property",  # position 58: Associated Taxes for Holding Property
    "net_sales_proceeds",  # position 59: Net Sales Proceeds
    "credit_enhancement_proceeds",  # position 60: Credit Enhancement Proceeds
    "repurchase_make_whole_proceeds",  # position 61: Repurchase Make Whole Proceeds
    "other_foreclosure_proceeds",  # position 62: Other Foreclosure Proceeds
    "modification_related_non_interest_bearing_upb",  # position 63: Modification-Related Non-Interest Bearing UPB
    "principal_forgiveness_amount",  # position 64: Principal Forgiveness Amount
    "original_list_start_date",  # position 65: Original List Start Date
    "original_list_price",  # position 66: Original List Price
    "current_list_start_date",  # position 67: Current List Start Date
    "current_list_price",  # position 68: Current List Price
    "borrower_credit_score_at_issuance",  # position 69: Borrower Credit Score At Issuance
    "co_borrower_credit_score_at_issuance",  # position 70: Co-Borrower Credit Score At Issuance
    "borrower_credit_score_current",  # position 71: Borrower Credit Score Current
    "co_borrower_credit_score_current",  # position 72: Co-Borrower Credit Score Current
    "mortgage_insurance_type",  # position 73: Mortgage Insurance Type
    "servicing_activity_indicator",  # position 74: Servicing Activity Indicator
    "current_period_modification_loss_amount",  # position 75: Current Period Modification Loss Amount
    "cumulative_modification_loss_amount",  # position 76: Cumulative Modification Loss Amount
    "current_period_credit_event_net_gain_or_loss",  # position 77: Current Period Credit Event Net Gain or Loss
    "cumulative_credit_event_net_gain_or_loss",  # position 78: Cumulative Credit Event Net Gain or Loss
    "special_eligibility_program",  # position 79: Special Eligibility Program
    "foreclosure_principal_write_off_amount",  # position 80: Foreclosure Principal Write-off Amount
    "relocation_mortgage_indicator",  # position 81: Relocation Mortgage Indicator
    "zero_balance_code_change_date",  # position 82: Zero Balance Code Change Date
    "loan_holdback_indicator",  # position 83: Loan Holdback Indicator
    "loan_holdback_effective_date",  # position 84: Loan Holdback Effective Date
    "delinquent_accrued_interest",  # position 85: Delinquent Accrued Interest
    "property_valuation_method",  # position 86: Property Valuation Method
    "high_balance_loan_indicator",  # position 87: High Balance Loan Indicator
    "arm_initial_fixed_rate_period_5_yr_indicator",  # position 88: ARM Initial Fixed-Rate Period  ≤ 5 YR Indicator
    "arm_product_type",  # position 89: ARM Product Type
    "initial_fixed_rate_period",  # position 90: Initial Fixed-Rate Period
    "interest_rate_adjustment_frequency",  # position 91: Interest Rate Adjustment Frequency
    "next_interest_rate_adjustment_date",  # position 92: Next Interest Rate Adjustment Date
    "next_payment_change_date",  # position 93: Next Payment Change Date
    "index",  # position 94: Index
    "arm_cap_structure",  # position 95: ARM Cap Structure
    "initial_interest_rate_cap_up_percent",  # position 96: Initial Interest Rate Cap Up Percent
    "periodic_interest_rate_cap_up_percent",  # position 97: Periodic Interest Rate Cap Up Percent
    "lifetime_interest_rate_cap_up_percent",  # position 98: Lifetime Interest Rate Cap Up Percent
    "mortgage_margin",  # position 99: Mortgage Margin
    "arm_balloon_indicator",  # position 100: ARM Balloon Indicator
    "arm_plan_number",  # position 101: ARM Plan Number
    "borrower_assistance_plan",  # position 102: Borrower Assistance Plan
    "high_loan_to_value_hltv_refinance_option_indicator",  # position 103: High Loan to Value (HLTV) Refinance Option Indicator
    "deal_name",  # position 104: Deal Name
    "repurchase_make_whole_proceeds_flag",  # position 105: Repurchase Make Whole Proceeds Flag
    "alternative_delinquency_resolution",  # position 106: Alternative Delinquency Resolution
    "alternative_delinquency_resolution_count",  # position 107: Alternative Delinquency Resolution Count
    "total_deferral_amount",  # position 108: Total Deferral Amount
    "payment_deferral_modification_event_indicator",  # position 109: Payment Deferral Modification Event Indicator
    "interest_bearing_upb",  # position 110: Interest Bearing UPB
    "origination_classic_fico",  # position 111: Origination Classic FICO®
    "issuance_classic_fico",  # position 112: Issuance Classic FICO®
    "current_classic_fico",  # position 113: Current Classic FICO®
    "origination_vantagescore_4_0",  # position 114: Origination VantageScore® 4.0
]

assert len(FILE_COLUMNS) == 114
assert len(set(FILE_COLUMNS)) == len(FILE_COLUMNS)
