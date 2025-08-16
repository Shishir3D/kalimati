import sys
import os
import time
import psycopg2
from pyspark.sql import SparkSession

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utility.utility import setup_logging


def create_spark_session():
    """Initialize Spark session."""
    return (
        SparkSession.builder.appName("KalimatiDataLoad")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "4g")
        .getOrCreate()
    )


def create_postgres_tables(pg_un, pg_pw, pg_host):
    """Stage 1: Create PostgreSQL tables if they don’t exist."""
    conn, cursor = None, None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=pg_un,
            password=pg_pw,
            host=pg_host,
            port="5432",
        )
        cursor = conn.cursor()

        create_table_query = """
            CREATE TABLE IF NOT EXISTS kalimati_master (
                name_original TEXT,
                name TEXT,
                type TEXT,
                color TEXT,
                location TEXT,
                date DATE,
                unit TEXT,
                maximum FLOAT,
                minimum FLOAT,
                average FLOAT
            );

            CREATE TABLE IF NOT EXISTS kalimati_prices_by_date (
                date DATE,
                name TEXT,
                avg_price FLOAT,
                avg_max FLOAT,
                avg_min FLOAT
            );

            CREATE TABLE IF NOT EXISTS kalimati_prices_by_location (
                location TEXT,
                name TEXT,
                avg_price FLOAT
            );

            CREATE TABLE IF NOT EXISTS kalimati_metadata (
                name_original TEXT,
                name TEXT,
                type TEXT,
                color TEXT,
                unit TEXT
            );
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("Stage 1: PostgreSQL tables created successfully")

    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def load_to_postgres(spark, input_dir, pg_un, pg_pw, pg_host):
    """Stage 2: Load parquet data into PostgreSQL tables."""

    jdbc_url = f"jdbc:postgresql://{pg_host}:5432/postgres"
    connection_properties = {
        "user": pg_un,
        "password": pg_pw,
        "driver": "org.postgresql.Driver",
    }

    try:
        # Load Master
        master_df = spark.read.parquet(os.path.join(input_dir, "stage2", "master_table"))
        master_df.write.mode("overwrite").jdbc(
            url=jdbc_url, table="kalimati_master", properties=connection_properties
        )

        # Load Prices by Date
        prices_by_date = spark.read.parquet(
            os.path.join(input_dir, "stage3", "prices_by_date")
        )
        prices_by_date.write.mode("overwrite").jdbc(
            url=jdbc_url, table="kalimati_prices_by_date", properties=connection_properties
        )

        # Load Prices by Location
        prices_by_location = spark.read.parquet(
            os.path.join(input_dir, "stage3", "prices_by_location")
        )
        prices_by_location.write.mode("overwrite").jdbc(
            url=jdbc_url, table="kalimati_prices_by_location", properties=connection_properties
        )

        # Load Metadata
        metadata = spark.read.parquet(os.path.join(input_dir, "stage3", "metadata"))
        metadata.write.mode("overwrite").jdbc(
            url=jdbc_url, table="kalimati_metadata", properties=connection_properties
        )

        print("Stage 2: Loaded all datasets into PostgreSQL")

    except Exception as e:
        print(f"Error loading data: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python load/execute.py <input_dir> <pg_un> <pg_pw> <pg_host>")
        sys.exit(1)

    input_dir = sys.argv[1]
    pg_un = sys.argv[2]
    pg_pw = sys.argv[3]
    pg_host = sys.argv[4]

    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist")
        sys.exit(1)

    start = time.time()
    spark = create_spark_session()

    create_postgres_tables(pg_un, pg_pw, pg_host)
    load_to_postgres(spark, input_dir, pg_un, pg_pw, pg_host)

    end = time.time()
    print(f"Load pipeline completed in {round(end-start,2)} seconds")
