from pyspark.sql import SparkSession
from pyspark.sql import functions as F

SILVER_PATH = "data/silver/fannie_mae/loan_performance.parquet"


def run():
    spark = (
        SparkSession.builder.appName("spot-check-flags")
        .master("local[*]")
        .getOrCreate()
    )
    df = spark.read.parquet(SILVER_PATH)

    print("Flag distribution:")
    df.groupBy("data_quality_flag").count().orderBy(F.desc("count")).show(
        truncate=False
    )

    flags = [
        r["data_quality_flag"]
        for r in df.select("data_quality_flag").distinct().collect()
        if r[0]
    ]
    for flag in flags:
        print(f"\n--- {flag} ---")
        df.filter(F.col("data_quality_flag") == flag).show(5, truncate=False)

    spark.stop()


if __name__ == "__main__":
    run()
