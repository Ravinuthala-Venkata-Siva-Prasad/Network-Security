import sys
import os
import numpy as np
import pandas as pd

from sklearn.impute import KNNImputer
from sklearn.pipeline import Pipeline

from src.constant.training_pipeline import (
    TARGET_COLUMN,
    DATA_TRANSFORMATION_IMPUTER_PARAMS
)

from src.entity.artifact_entity import (
    DataTransformationArtifact,
    DataValidationArtifact
)

from src.entity.config_entity import DataTransformationConfig

from src.exception.exception import NetworkSecurityException

from src.logging.logger import logging

from src.utils.main_utils.utils import (
    save_numpy_array_data,
    save_object
)


class DataTransformation:

    def __init__(
        self,
        data_validation_artifact: DataValidationArtifact,
        data_transformation_config: DataTransformationConfig
    ):
        try:
            self.data_validation_artifact = data_validation_artifact

            self.data_transformation_config = data_transformation_config

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # Read CSV Data
    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            logging.info(f"Reading data from {file_path}")

            return pd.read_csv(file_path)

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # Create Data Transformer Object
    def get_data_transformer_object(self) -> Pipeline:

        logging.info(
            "Entered get_data_transformer_object method"
        )

        try:
            imputer: KNNImputer = KNNImputer(
                **DATA_TRANSFORMATION_IMPUTER_PARAMS
            )

            logging.info(
                f"Initialized KNNImputer with "
                f"{DATA_TRANSFORMATION_IMPUTER_PARAMS}"
            )

            processor: Pipeline = Pipeline(
                [
                    ("imputer", imputer)
                ]
            )

            return processor

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # Initiate Data Transformation
    def initiate_data_transformation(self) -> DataTransformationArtifact:

        logging.info(
            "Entered initiate_data_transformation method"
        )

        try:

            logging.info("Starting Data Transformation")

            # Step 1: Read training and testing data
            train_df = DataTransformation.read_data(
                self.data_validation_artifact.valid_train_file_path
            )

            test_df = DataTransformation.read_data(
                self.data_validation_artifact.valid_test_file_path
            )

            logging.info(
                f"Training Data Shape: {train_df.shape}"
            )

            logging.info(
                f"Testing Data Shape: {test_df.shape}"
            )

            # Step 2: Separate input and target features

            if TARGET_COLUMN not in train_df.columns:
                raise ValueError(
                    f"Target column '{TARGET_COLUMN}' not found "
                    "in training dataset"
                )

            if TARGET_COLUMN not in test_df.columns:
                raise ValueError(
                    f"Target column '{TARGET_COLUMN}' not found "
                    "in testing dataset"
                )

            input_feature_train_df = train_df.drop(
                columns=[TARGET_COLUMN]
            )

            target_feature_train_df = train_df[TARGET_COLUMN]

            input_feature_test_df = test_df.drop(
                columns=[TARGET_COLUMN]
            )

            target_feature_test_df = test_df[TARGET_COLUMN]

            # Step 3: Replace target labels
            target_feature_train_df = (
                target_feature_train_df.replace(-1, 0)
            )

            target_feature_test_df = (
                target_feature_test_df.replace(-1, 0)
            )

            # Step 4: Create preprocessor
            preprocessor = self.get_data_transformer_object()

            # Step 5: Fit on training data only
            preprocessor_object = preprocessor.fit(
                input_feature_train_df
            )

            # Step 6: Transform training data
            transformed_input_train_feature = (
                preprocessor_object.transform(
                    input_feature_train_df
                )
            )

            # Step 7: Transform testing data
            transformed_input_test_feature = (
                preprocessor_object.transform(
                    input_feature_test_df
                )
            )

            # Step 8: Combine input and target features
            train_arr = np.c_[
                transformed_input_train_feature,
                np.array(target_feature_train_df)
            ]

            test_arr = np.c_[
                transformed_input_test_feature,
                np.array(target_feature_test_df)
            ]

            logging.info(
                f"Transformed Training Shape: {train_arr.shape}"
            )

            logging.info(
                f"Transformed Testing Shape: {test_arr.shape}"
            )

            # Step 9: Save transformed datasets
            save_numpy_array_data(
                self.data_transformation_config.transformed_train_file_path,
                array=train_arr
            )

            save_numpy_array_data(
                self.data_transformation_config.transformed_test_file_path,
                array=test_arr
            )

            # Step 10: Save preprocessor object
            save_object(
                self.data_transformation_config.transformed_object_file_path,
                preprocessor_object
            )

            # Step 11: Save final preprocessor
            save_object(
                "final_model/preprocessor.pkl",
                preprocessor_object
            )

            # Step 12: Create Data Transformation Artifact
            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=(
                    self.data_transformation_config.transformed_object_file_path
                ),
                transformed_train_file_path=(
                    self.data_transformation_config.transformed_train_file_path
                ),
                transformed_test_file_path=(
                    self.data_transformation_config.transformed_test_file_path
                )
            )

            logging.info(
                "Data Transformation completed successfully"
            )

            print("\n========== DATA TRANSFORMATION COMPLETED ==========")

            print("Training Array Shape:", train_arr.shape)

            print("Testing Array Shape:", test_arr.shape)

            print(
                "Preprocessor File:",
                self.data_transformation_config.transformed_object_file_path
            )

            print("===================================================")

            return data_transformation_artifact

        except Exception as e:

            raise NetworkSecurityException(e, sys)