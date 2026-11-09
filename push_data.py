import os
import sys
from pathlib import Path

import certifi
import pandas as pd
import pymongo

from dotenv import load_dotenv

from src.exception.exception import NetworkSecurityException
from src.logging.logger import logging


# Load environment variables
ROOT_DIR = Path(__file__).resolve().parent

load_dotenv(ROOT_DIR / ".env")

MONGO_DB_URL = os.getenv("MONGO_DB_URL")

ca = certifi.where()


class NetworkDataExtract:

    def __init__(self):
        try:
            logging.info("NetworkDataExtract initialized")

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # CSV to JSON conversion
    def csv_to_json_convertor(self, file_path):

        try:

            logging.info("CSV conversion started")

            data = pd.read_csv(file_path)

            records = data.to_dict(orient="records")

            logging.info(
                f"CSV converted successfully. Total records: {len(records)}"
            )

            return records

        except Exception as e:

            logging.exception("Error during CSV conversion")

            raise NetworkSecurityException(e, sys)

    # Insert records into MongoDB
    def insert_data_mongodb(self, records, database, collection):

        try:

            if not MONGO_DB_URL:
                raise ValueError("MONGO_DB_URL not found in .env")

            if not records:
                raise ValueError("No records available for insertion")

            logging.info("MongoDB connection started")

            self.mongo_client = pymongo.MongoClient(
                MONGO_DB_URL,
                tlsCAFile=ca,
                serverSelectionTimeoutMS=10000
            )

            # Verify connection
            self.mongo_client.admin.command("ping")

            logging.info("MongoDB connected successfully")

            self.database = self.mongo_client[database]

            self.collection = self.database[collection]

            # Insert records
            result = self.collection.insert_many(records)

            inserted_count = len(result.inserted_ids)

            logging.info(
                f"Successfully inserted {inserted_count} records"
            )

            return inserted_count

        except Exception as e:

            logging.exception("MongoDB insertion failed")

            raise NetworkSecurityException(e, sys)

        finally:

            if hasattr(self, "mongo_client"):
                self.mongo_client.close()


if __name__ == '__main__':

    try:

        FILE_PATH = "data/phisingData.csv"

        DATABASE = "Network_Security"

        Collection = "NetworkData"

        networkobj = NetworkDataExtract()

        # Convert CSV to records
        records = networkobj.csv_to_json_convertor(
            file_path=FILE_PATH
        )

        print("Total CSV records:", len(records))

        # Insert into MongoDB
        no_of_records = networkobj.insert_data_mongodb(
            records,
            DATABASE,
            Collection
        )

        print("Successfully inserted records:", no_of_records)

    except Exception as e:

        logging.exception("Application failed")

        print(e)