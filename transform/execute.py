import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql import types as T
from pyspark.sql import functions as F
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utility.utility import setup_logging


def create_spark_session():
    """Initialize Spark session."""
    return (
        SparkSession.builder.appName("SpotifyDataTransform")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "4g")
        .getOrCreate()
    )

def load_and_clean(spark, input_dir, output_dir):
    """Stage 1: Load data, drop duplicates, remove nulls, save cleaned data."""

    schema = T.StructType(
        [
            T.StructField("name_original", T.StringType(), False),
            T.StructField("name", T.StringType(), True),
            T.StructField("type", T.StringType(), True),
            T.StructField("color", T.StringType(), True),
            T.StructField("location", T.StringType(), True),
            T.StructField("date", T.DateType(), True),
            T.StructField("unit", T.StringType(), True),
            T.StructField("maximum", T.FloatType(), True),
            T.StructField("minimum", T.FloatType(), True),
            T.StructField("average", T.FloatType(), True),
        ]
    )

    df = spark.read.schema(schema).csv(
        os.path.join(input_dir, "kalimati.csv"), header=True
    )

    # Clean
    df = df.dropDuplicates(
        ["name_original", "date", "location"]
    ).filter(F.col("name_original").isNotNull())

    # Save
    df.write.mode("overwrite").parquet(os.path.join(output_dir, "stage1", "cleaned"))

    print("Stage 1: Cleaned data saved")
    return df


def create_master_table(output_dir, df):
    """Stage 2: Create master table for analysis."""

    master_df = df.select(
        "name_original",
        "name",
        "type",
        "color",
        "location",
        "date",
        "unit",
        "maximum",
        "minimum",
        "average",
    )

    master_df.write.mode("overwrite").parquet(
        os.path.join(output_dir, "stage2", "master_table")
    )
    print("Stage 2: Master table saved")
    return master_df


def create_query_tables(output_dir, df):
    """Stage 3: Create query-optimized tables."""

    # Prices by date
    prices_by_date = df.groupBy("date", "name").agg(
        F.avg("average").alias("avg_price"),
        F.avg("maximum").alias("avg_max"),
        F.avg("minimum").alias("avg_min"),
    )
    prices_by_date.write.mode("overwrite").parquet(
        os.path.join(output_dir, "stage3", "prices_by_date")
    )

    # Prices by location
    prices_by_location = df.groupBy("location", "name").agg(
        F.avg("average").alias("avg_price")
    )
    prices_by_location.write.mode("overwrite").parquet(
        os.path.join(output_dir, "stage3", "prices_by_location")
    )

    # Metadata table (unique product info)
    metadata = df.select("name_original", "name", "type", "color", "unit").dropDuplicates()
    metadata.write.mode("overwrite").parquet(
        os.path.join(output_dir, "stage3", "metadata")
    )

    print("Stage 3: Query-optimized tables saved")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python transform.py <input_dir> <output_dir>"
        )
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]


    spark = create_spark_session()

    df = load_and_clean(spark, input_dir, output_dir)
    master_df = create_master_table(output_dir, df)
    create_query_tables(output_dir, df)

    print("Transformation pipeline completed")
