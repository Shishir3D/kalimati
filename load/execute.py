import time
import sys
import os
import psycopg2
from psycopg2 import sql
from pyspark.sql import SparkSession

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


def create_postgres_tables(logger, pg_un, pg_pw, pg_host):
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=pg_un,
            password=pg_pw,
            host=pg_host,
            port="5432",
        )
        cursor = conn.cursor()

        # Adjust schema for Kalimati dataset
        create_table_query = """
            CREATE TABLE IF NOT EXISTS kalimati_prices (
                date DATE,
                commodity TEXT,
                unit TEXT,
                minimum_price FLOAT,
                maximum_price FLOAT,
                average_price FLOAT
            );
        """

        cursor.execute(create_table_query)
        conn.commit()
        logger.info("PostgreSQL table for Kalimati dataset created successfully")

    except Exception as e:
        logger.error(f"Error creating table: {e}")
    finally:
        if cursor:  # type: ignore
            cursor.close()
        if conn:
            conn.close()


def load_to_postgres(logger, spark, input_dir, pg_un, pg_pw, pg_host):
    jdbc_url = f"jdbc:postgresql://{pg_host}:5432/postgres"
    connection_properties = {
        "user": pg_un,
        "password": pg_pw,
        "driver": "org.postgresql.Driver",
    }

    try:
        # Assuming parquet file(s) inside input_dir/kalimati/
        df = spark.read.parquet(os.path.join(input_dir, "kalimati"))
        df.write.mode("overwrite").jdbc(
            url=jdbc_url, table="kalimati_prices", properties=connection_properties
        )
        logger.info("Loaded Kalimati dataset to PostgreSQL")
    except Exception as e:
        logger.error(f"Error loading Kalimati dataset: {e}")


if __name__ == "__main__":

    logger = setup_logging("load.log")

    if len(sys.argv) != 9:
        logger.critical(
            "Usage: python load/execute.py <input_dir> <pg_un> <pg_pw> <pg_host>"
        )
        sys.exit(1)

    logger.info("Load stage started")
    start = time.time()

    input_dir = sys.argv[1]
    pg_un = sys.argv[2]
    pg_pw = sys.argv[3]
    pg_host = sys.argv[4]

    if not os.path.exists(input_dir):
        logger.error(f"Error: Input directory {input_dir} does not exist")
        sys.exit(1)

    spark = create_spark_session()
    create_postgres_tables(logger, pg_un, pg_pw, pg_host)
    load_to_postgres(logger, spark, input_dir, pg_un, pg_pw, pg_host)

    end = time.time()
    logger.info(f"Load stage completed in {round(end-start,2)} seconds")
