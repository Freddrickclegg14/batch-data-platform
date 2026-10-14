from pathlib import Path

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType

from spark_jobs.fannie_mae_silver_columns import SILVER_COLUMNS, CRITICAL_FIELDS

bronze_dir = Path("data/raw/fannie_mae")
silver_dir = Path("data/silver/fannie_mae")


def cast_columns(df: DataFrame) -> DataFrame:
    select_exprs = []
    for col_name, target_type in SILVER_COLUMNS:
        if target_type == "date":
            expr = F.to_date(F.col(col_name), "MMyyyy").alias(col_name)
        elif target_type == "int":
            expr = F.col(col_name).cast(IntegerType()).alias(col_name)
        elif target_type == "double":
            expr = F.col(col_name).cast(DoubleType()).alias(col_name)
        else:
            expr = F.col(col_name).alias(col_name)
        select_exprs.append(expr)

    vintage_expr = F.regexp_extract(F.input_file_name(), r"(\d{4}Q[1-4])", 1).alias(
        "vintage_quarter"
    )
    select_exprs.append(vintage_expr)

    return df.select(*select_exprs)


def quality_flags(df: DataFrame) -> DataFrame:
    checked_fields = {
        "loan_identifier",
        "monthly_reporting_period",
        "original_upb",
        "current_actual_upb",
        "original_interest_rate",
        "current_interest_rate",
        "loan_age",
        "original_loan_to_value_ratio_ltv",
        "debt_to_income_dti",
        "borrower_credit_score_at_origination",
        "property_state",
        "channel",
        "occupancy_status",
        "zero_balance_code",
        "current_loan_delinquency_status",
    }
    assert checked_fields == set(CRITICAL_FIELDS), (
        f"quality_flags checks and CRITICAL_FIELDS have drifted apart.\n"
        f"In checks but not CRITICAL_FIELDS: {checked_fields - set(CRITICAL_FIELDS)}\n"
        f"In CRITICAL_FIELDS but not checks: {set(CRITICAL_FIELDS) - checked_fields}"
    )
    df = df.withColumn(
        "data_quality_flag",
        F.when(
            F.col("loan_identifier").isNull(),
            F.lit("missing_loan_id"),
        )
        .when(
            F.col("monthly_reporting_period").isNull(),
            F.lit("No_reporting_period"),
        )
        .when(
            F.col("original_upb").isNull() | (F.col("original_upb") <= 0),
            F.lit("invalid_original_upb"),
        )
        .when(
            F.col("current_actual_upb").isNull() | (F.col("current_actual_upb") < 0),
            F.lit("negative_current_upb"),
        )
        .when(
            F.col("original_interest_rate").isNull()
            | (F.col("original_interest_rate") < 0)
            | (F.col("original_interest_rate") > 25),
            F.lit("invalid_interest_rate"),
        )
        .when(
            F.col("loan_age").isNull() | (F.col("loan_age") < 0),
            F.lit("negative_loan_age"),
        )
        .when(
            F.col("original_loan_to_value_ratio_ltv").isNull()
            | (F.col("original_loan_to_value_ratio_ltv") < 0)
            | (F.col("original_loan_to_value_ratio_ltv") > 200),
            F.lit("invalid_ltv"),
        )
        .when(
            F.col("debt_to_income_dti").isNull()
            | (F.col("debt_to_income_dti") < 0)
            | (F.col("debt_to_income_dti") > 100),
            F.lit("invalid_dti"),
        )
        .when(
            F.col("borrower_credit_score_at_origination").isNull()
            | (F.col("borrower_credit_score_at_origination") < 300)
            | (F.col("borrower_credit_score_at_origination") > 850),
            F.lit("invalid_credit_score"),
        )
        .when(
            F.col("property_state").isNull() | (F.length(F.col("property_state")) != 2),
            F.lit("invalid_state_code"),
        )
        .when(
            F.col("channel").isNull() | (~F.col("channel").isin("R", "C", "B")),
            F.lit("invalid_channel"),
        )
        .when(
            F.col("occupancy_status").isNull()
            | (~F.col("occupancy_status").isin("P", "S", "I")),
            F.lit("invalid_occapancy_status"),
        )
        .when(
            F.col("zero_balance_code").isNotNull()
            & (F.col("zero_balance_code") != "")
            & (
                ~F.col("zero_balance_code").isin(
                    "01", "02", "03", "06", "09", "15", "16", "96", "97"
                )
            ),
            F.lit("invalid_zero_balance_code"),
        )
        .when(
            F.col("current_loan_delinquency_status").isNull()
            | (
                (F.col("current_loan_delinquency_status") != "XX")
                & (
                    F.col("current_loan_delinquency_status")
                    .cast(IntegerType())
                    .isNull()
                )
            ),
            F.lit("invalid_current_loan_delinquency_status"),
        )
        .when(
            F.col("current_interest_rate").isNull()
            | (F.col("current_interest_rate") < 0)
            | (F.col("current_interest_rate") > 25),
            F.lit("invalid_current_interest_rate"),
        )
        .otherwise(F.lit(None)),
    )

    return df


def run() -> dict:
    spark = (
        SparkSession.builder.appName("fannie-mae-bronze-to-silver")
        .master("local[*]")
        .getOrCreate()
    )

    bronze_files = sorted(bronze_dir.glob("*.parquet"))
    if not bronze_files:
        raise FileNotFoundError(f"No Bronze files found in {bronze_dir}")

    print(f"Reading {len(bronze_files)} Bronze file(s) from {bronze_dir}")
    df = spark.read.parquet(*[str(f) for f in bronze_files])
    bronze_count = df.count()
    print(f"Bronze row count: {bronze_count:,}")

    silver_df = cast_columns(df)
    silver_df = quality_flags(silver_df)

    flagged_count = silver_df.filter(F.col("data_quality_flag").isNotNull()).count()
    print(
        f"Rows flagged by a critical-field check: {flagged_count:,} ({flagged_count / bronze_count:.2%})"
    )

    silver_dir.mkdir(parents=True, exist_ok=True)
    out_path = silver_dir / "loan_performance.parquet"
    silver_df.write.mode("overwrite").parquet(str(out_path))

    silver_count = silver_df.count()
    print(
        f"Wrote {silver_count:,} rows, {len(SILVER_COLUMNS) + 2} columns to {out_path}"
    )

    spark.stop()

    return {
        "bronze_count": bronze_count,
        "silver_count": silver_count,
        "flagged_count": flagged_count,
    }


if __name__ == "__main__":
    run()
