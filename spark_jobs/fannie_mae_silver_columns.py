"""
Silver-layer column config for Fannie Mae loan performance data.

Only the 73 fields applicable to Single-Family Loan Performance are
kept (the other 41 glossary fields are CAS/CIRT-only and always blank
in this dataset -- dropped at Bronze -> Silver, not carried forward).

Each entry maps the Bronze (string) column name to its target Silver
type. DATE fields are MMYYYY strings in Bronze, parsed to real dates.
CRITICAL_FIELDS are the ~15 fields with strict validation in the
transform; everything else is type-cast only, no business rules.
"""

SILVER_COLUMNS = [
    ("loan_identifier", "string"),  # position 2: Loan Identifier (ALPHA-NUMERIC, X(12))
    (
        "monthly_reporting_period",
        "date",
    ),  # position 3: Monthly Reporting Period (DATE, MMYYYY)
    ("channel", "string"),  # position 4: Channel (ALPHA-NUMERIC, X(1))
    ("seller_name", "string"),  # position 5: Seller Name (ALPHA-NUMERIC, X(50))
    ("servicer_name", "string"),  # position 6: Servicer Name (ALPHA-NUMERIC, X(50))
    (
        "original_interest_rate",
        "double",
    ),  # position 8: Original Interest Rate (NUMERIC, 9(2).999)
    (
        "current_interest_rate",
        "double",
    ),  # position 9: Current Interest Rate (NUMERIC, 9(2).999)
    ("original_upb", "double"),  # position 10: Original UPB (NUMERIC, 9(10).99)
    (
        "current_actual_upb",
        "double",
    ),  # position 12: Current Actual UPB (NUMERIC, 9(10).99)
    ("original_loan_term", "int"),  # position 13: Original Loan Term (NUMERIC, 9(3))
    ("origination_date", "date"),  # position 14: Origination Date (DATE, MMYYYY)
    ("first_payment_date", "date"),  # position 15: First Payment Date (DATE, MMYYYY)
    ("loan_age", "int"),  # position 16: Loan Age (NUMERIC, 9(3))
    (
        "remaining_months_to_legal_maturity",
        "int",
    ),  # position 17: Remaining Months to Legal Maturity (NUMERIC, 9(3))
    (
        "remaining_months_to_maturity",
        "int",
    ),  # position 18: Remaining Months To Maturity (NUMERIC, 9(3))
    ("maturity_date", "date"),  # position 19: Maturity Date (DATE, MMYYYY)
    (
        "original_loan_to_value_ratio_ltv",
        "int",
    ),  # position 20: Original Loan to Value Ratio (LTV) (NUMERIC, 9(3))
    (
        "original_combined_loan_to_value_ratio_cltv",
        "int",
    ),  # position 21: Original Combined Loan to Value Ratio (CLTV) (NUMERIC, 9(3))
    ("number_of_borrowers", "int"),  # position 22: Number of Borrowers (NUMERIC, 9(2))
    ("debt_to_income_dti", "int"),  # position 23: Debt-To-Income (DTI) (NUMERIC, 9(2))
    (
        "borrower_credit_score_at_origination",
        "int",
    ),  # position 24: Borrower Credit Score at Origination (NUMERIC, 9(3))
    (
        "co_borrower_credit_score_at_origination",
        "int",
    ),  # position 25: Co-Borrower Credit Score at Origination (NUMERIC, 9(3))
    (
        "first_time_home_buyer_indicator",
        "string",
    ),  # position 26: First Time Home Buyer Indicator (ALPHA-NUMERIC, X(1))
    ("loan_purpose", "string"),  # position 27: Loan Purpose (ALPHA-NUMERIC, X(1))
    ("property_type", "string"),  # position 28: Property Type (ALPHA-NUMERIC, X(2))
    ("number_of_units", "int"),  # position 29: Number of Units (NUMERIC, 9(1))
    (
        "occupancy_status",
        "string",
    ),  # position 30: Occupancy Status (ALPHA-NUMERIC, X(1))
    ("property_state", "string"),  # position 31: Property State (ALPHA-NUMERIC, X(2))
    (
        "metropolitan_statistical_area_msa_or_metropolitan_statistical_division_area_msda",
        "string",
    ),  # position 32: Metropolitan Statistical Area (MSA) or Metropolitan Statistical Division Area (MSDA) (ALPHA-NUMERIC, X(5))
    ("zip_code_short", "string"),  # position 33: Zip Code Short (ALPHA-NUMERIC, X(3))
    (
        "mortgage_insurance_percentage",
        "double",
    ),  # position 34: Mortgage Insurance Percentage (NUMERIC, 9(3).99)
    (
        "amortization_type",
        "string",
    ),  # position 35: Amortization Type (ALPHA-NUMERIC, X(3))
    (
        "prepayment_penalty_indicator",
        "string",
    ),  # position 36: Prepayment Penalty Indicator (ALPHA-NUMERIC, X(1))
    (
        "interest_only_loan_indicator",
        "string",
    ),  # position 37: Interest Only Loan Indicator (ALPHA-NUMERIC, X(1))
    (
        "interest_only_first_principal_and_interest_payment_date",
        "date",
    ),  # position 38: Interest Only First Principal And Interest Payment Date (DATE, MMYYYY)
    (
        "months_to_amortization",
        "int",
    ),  # position 39: Months to Amortization (NUMERIC, 9(3))
    (
        "current_loan_delinquency_status",
        "string",
    ),  # position 40: Current Loan Delinquency Status (ALPHA-NUMERIC, X(2))
    (
        "loan_payment_history",
        "string",
    ),  # position 41: Loan Payment History (ALPHA-NUMERIC, X(48))
    (
        "modification_flag",
        "string",
    ),  # position 42: Modification Flag (ALPHA-NUMERIC, X(1))
    (
        "zero_balance_code",
        "string",
    ),  # position 44: Zero Balance Code (ALPHA-NUMERIC, X(3))
    (
        "zero_balance_effective_date",
        "date",
    ),  # position 45: Zero Balance Effective Date (DATE, MMYYYY)
    (
        "upb_at_the_time_of_removal",
        "double",
    ),  # position 46: UPB at the Time of Removal (NUMERIC, 9(10).99)
    (
        "total_principal_current",
        "double",
    ),  # position 49: Total Principal Current (NUMERIC, 9(10).99)
    (
        "last_paid_installment_date",
        "date",
    ),  # position 51: Last Paid Installment Date (DATE, MMYYYY)
    ("foreclosure_date", "date"),  # position 52: Foreclosure Date (DATE, MMYYYY)
    ("disposition_date", "date"),  # position 53: Disposition Date (DATE, MMYYYY)
    (
        "foreclosure_costs",
        "double",
    ),  # position 54: Foreclosure Costs (NUMERIC, 9(10).99)
    (
        "property_preservation_and_repair_costs",
        "double",
    ),  # position 55: Property Preservation and Repair Costs (NUMERIC, 9(10).99)
    (
        "asset_recovery_costs",
        "double",
    ),  # position 56: Asset Recovery Costs (NUMERIC, 9(10).99)
    (
        "miscellaneous_holding_expenses_and_credits",
        "double",
    ),  # position 57: Miscellaneous Holding Expenses and Credits (NUMERIC, 9(10).99)
    (
        "associated_taxes_for_holding_property",
        "double",
    ),  # position 58: Associated Taxes for Holding Property (NUMERIC, 9(10).99)
    (
        "net_sales_proceeds",
        "double",
    ),  # position 59: Net Sales Proceeds (NUMERIC, 9(10).99)
    (
        "credit_enhancement_proceeds",
        "double",
    ),  # position 60: Credit Enhancement Proceeds (NUMERIC, 9(10).99)
    (
        "repurchase_make_whole_proceeds",
        "double",
    ),  # position 61: Repurchase Make Whole Proceeds (NUMERIC, 9(10).99)
    (
        "other_foreclosure_proceeds",
        "double",
    ),  # position 62: Other Foreclosure Proceeds (NUMERIC, 9(10).99)
    (
        "modification_related_non_interest_bearing_upb",
        "double",
    ),  # position 63: Modification-Related Non-Interest Bearing UPB (NUMERIC, 9(10).99)
    (
        "principal_forgiveness_amount",
        "double",
    ),  # position 64: Principal Forgiveness Amount (NUMERIC, 9(10).99)
    (
        "mortgage_insurance_type",
        "string",
    ),  # position 73: Mortgage Insurance Type (ALPHA-NUMERIC, X(1))
    (
        "servicing_activity_indicator",
        "string",
    ),  # position 74: Servicing Activity Indicator (ALPHA-NUMERIC, X(1))
    (
        "special_eligibility_program",
        "string",
    ),  # position 79: Special Eligibility Program (ALPHA-NUMERIC, X(1))
    (
        "foreclosure_principal_write_off_amount",
        "double",
    ),  # position 80: Foreclosure Principal Write-off Amount (NUMERIC, 9(10).99)
    (
        "relocation_mortgage_indicator",
        "string",
    ),  # position 81: Relocation Mortgage Indicator (ALPHA-NUMERIC, X(1))
    (
        "property_valuation_method",
        "string",
    ),  # position 86: Property Valuation Method (ALPHA-NUMERIC, X(1))
    (
        "high_balance_loan_indicator",
        "string",
    ),  # position 87: High Balance Loan Indicator (ALPHA-NUMERIC, X(1))
    (
        "borrower_assistance_plan",
        "string",
    ),  # position 102: Borrower Assistance Plan (ALPHA-NUMERIC, X(1))
    (
        "high_loan_to_value_hltv_refinance_option_indicator",
        "string",
    ),  # position 103: High Loan to Value (HLTV) Refinance Option Indicator (ALPHA-NUMERIC, X(1))
    (
        "repurchase_make_whole_proceeds_flag",
        "string",
    ),  # position 105: Repurchase Make Whole Proceeds Flag (ALPHA-NUMERIC, X(1))
    (
        "alternative_delinquency_resolution",
        "string",
    ),  # position 106: Alternative Delinquency Resolution (ALPHA-NUMERIC, X(1))
    (
        "alternative_delinquency_resolution_count",
        "int",
    ),  # position 107: Alternative Delinquency Resolution Count (NUMERIC, 9(3))
    (
        "total_deferral_amount",
        "double",
    ),  # position 108: Total Deferral Amount (NUMERIC, 9(10).99)
    (
        "payment_deferral_modification_event_indicator",
        "string",
    ),  # position 109: Payment Deferral Modification Event Indicator (ALPHA-NUMERIC, X(1))
    (
        "origination_classic_fico",
        "int",
    ),  # position 111: Origination Classic FICO® (NUMERIC, 9(3))
    (
        "origination_vantagescore_4_0",
        "int",
    ),  # position 114: Origination VantageScore® 4.0 (NUMERIC, 9(3))
]

CRITICAL_FIELDS = [
    "borrower_credit_score_at_origination",
    "channel",
    "current_actual_upb",
    "current_interest_rate",
    "current_loan_delinquency_status",
    "debt_to_income_dti",
    "loan_age",
    "loan_identifier",
    "monthly_reporting_period",
    "occupancy_status",
    "original_interest_rate",
    "original_loan_to_value_ratio_ltv",
    "original_upb",
    "property_state",
    "zero_balance_code",
]

_names = [c[0] for c in SILVER_COLUMNS]
assert len(_names) == 73
assert len(set(_names)) == len(_names), "duplicate column names"
assert (
    CRITICAL_FIELDS <= set(_names)
    if False
    else all(c in _names for c in CRITICAL_FIELDS)
), "critical field missing from SILVER_COLUMNS"
