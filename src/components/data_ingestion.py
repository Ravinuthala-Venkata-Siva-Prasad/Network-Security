from src.exception.exception import NetworkSecurityException
from src.logging.logger import logging

from src.entity.config_entity import DataIngestionConfig
from src.entity.artifact_entity import DataIngestionArtifact

import os
import sys
import numpy as np
import pandas as pd
import pymongo

from sklearn.model_selection import train_test_split
from dotenv import load_dotenv

load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")


class DataIngestion:

    def __init__(self, data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # 1. Export MongoDB Collection as DataFrame
    def export_collection_as_dataframe(self):
        try:
            logging.info("Starting MongoDB data extraction")

            database_name = self.data_ingestion_config.database_name
            collection_name = self.data_ingestion_config.collection_name

            print("Database Name:", database_name)
            print("Collection Name:", collection_name)

            if not MONGO_DB_URL:
                raise Exception(
                    "MONGO_DB_URL is missing. Check your .env file."
                )

            self.mongo_client = pymongo.MongoClient(
                MONGO_DB_URL,
                serverSelectionTimeoutMS=10000
            )

            self.mongo_client.admin.command("ping")

            logging.info("MongoDB connected successfully")
            print("MongoDB connected successfully!")

            # Correct database and collection selection
            database = self.mongo_client[database_name]
            collection = database[collection_name]

            data = list(collection.find())

            print("Total documents fetched:", len(data))

            if len(data) == 0:
                raise Exception(
                    f"No documents found in database '{database_name}' "
                    f"and collection '{collection_name}'."
                )

            dataframe = pd.DataFrame(data)

            if "_id" in dataframe.columns:
                dataframe.drop(columns=["_id"], inplace=True)

            dataframe.replace({"na": np.nan}, inplace=True)

            print("DataFrame Shape:", dataframe.shape)
            print("Columns:", dataframe.columns.tolist())

            logging.info(
                f"Data extracted successfully. Shape: {dataframe.shape}"
            )

            return dataframe

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # 2. Export Data into Feature Store
    def export_data_into_feature_store(self, dataframe: pd.DataFrame):
        try:
            logging.info("Exporting data into feature store")

            feature_store_file_path = (
                self.data_ingestion_config.feature_store_file_path
            )

            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)

            dataframe.to_csv(
                feature_store_file_path,
                index=False,
                header=True
            )

            logging.info(
                f"Data successfully saved to {feature_store_file_path}"
            )

            print("Feature store created successfully!")

            return dataframe

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # 3. Split Data into Train and Test
    def split_data_as_train_test(self, dataframe: pd.DataFrame):
        try:
            logging.info("Starting train test split")

            if dataframe.empty:
                raise ValueError("Cannot split an empty DataFrame.")

            test_size = (
                self.data_ingestion_config.train_test_split_ratio
            )

            if not 0 < test_size < 1:
                raise ValueError(
                    "Train test split ratio must be between 0 and 1."
                )

            train_set, test_set = train_test_split(
                dataframe,
                test_size=test_size,
                random_state=42
            )

            logging.info("Train test split completed successfully")

            train_dir = os.path.dirname(
                self.data_ingestion_config.training_file_path
            )

            os.makedirs(train_dir, exist_ok=True)

            train_set.to_csv(
                self.data_ingestion_config.training_file_path,
                index=False,
                header=True
            )

            test_set.to_csv(
                self.data_ingestion_config.testing_file_path,
                index=False,
                header=True
            )

            print("Training data shape:", train_set.shape)
            print("Testing data shape:", test_set.shape)

            logging.info("Training and testing datasets exported")

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # 4. Initiate Data Ingestion
    def initiate_data_ingestion(self):
        try:
            logging.info("Entered initiate_data_ingestion method")

            # Step 1: Extract data from MongoDB
            dataframe = self.export_collection_as_dataframe()

            # Step 2: Save data into feature store
            dataframe = self.export_data_into_feature_store(dataframe)

            # Step 3: Split data into train and test
            self.split_data_as_train_test(dataframe)

            # Step 4: Create Data Ingestion Artifact
            data_ingestion_artifact = DataIngestionArtifact(
                trained_file_path=(
                    self.data_ingestion_config.training_file_path
                ),
                test_file_path=(
                    self.data_ingestion_config.testing_file_path
                )
            )

            logging.info("Data ingestion completed successfully")

            print("\n========== DATA INGESTION COMPLETED ==========")

            print(
                "Training File:",
                self.data_ingestion_config.training_file_path
            )

            print(
                "Testing File:",
                self.data_ingestion_config.testing_file_path
            )

            print("===============================================")

            return data_ingestion_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)

        finally:
            if hasattr(self, "mongo_client"):
                self.mongo_client.close()