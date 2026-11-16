from src.components.data_ingestion import DataIngestion
from src.components.data_validation import DataValidation
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer
from src.components.model_evaluation import ModelEvaluation

from src.entity.config_entity import (
    TrainingPipelineConfig,
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelEvaluationConfig
)

from src.exception.exception import NetworkSecurityException
from src.logging.logger import logging

import sys


if __name__ == '__main__':

    try:

        # ==========================================
        # STEP 1: TRAINING PIPELINE CONFIGURATION
        # ==========================================

        training_pipeline_config = TrainingPipelineConfig()

        # ==========================================
        # STEP 2: DATA INGESTION
        # ==========================================

        logging.info("Starting Data Ingestion")

        data_ingestion_config = DataIngestionConfig(
            training_pipeline_config
        )

        data_ingestion = DataIngestion(
            data_ingestion_config
        )

        data_ingestion_artifact = (
            data_ingestion.initiate_data_ingestion()
        )

        print(data_ingestion_artifact)

        logging.info("Data Ingestion Completed")

        # ==========================================
        # STEP 3: DATA VALIDATION
        # ==========================================

        logging.info("Starting Data Validation")

        data_validation_config = DataValidationConfig(
            training_pipeline_config
        )

        data_validation = DataValidation(
            data_ingestion_artifact,
            data_validation_config
        )

        data_validation_artifact = (
            data_validation.initiate_data_validation()
        )

        print(data_validation_artifact)

        logging.info("Data Validation Completed")

        # ==========================================
        # STEP 4: DATA TRANSFORMATION
        # ==========================================

        logging.info("Starting Data Transformation")

        data_transformation_config = DataTransformationConfig(
            training_pipeline_config
        )

        data_transformation = DataTransformation(
            data_validation_artifact,
            data_transformation_config
        )

        data_transformation_artifact = (
            data_transformation.initiate_data_transformation()
        )

        print(data_transformation_artifact)

        logging.info("Data Transformation Completed")

        # ==========================================
        # STEP 5: MODEL TRAINING
        # ==========================================

        logging.info("Starting Model Training")

        model_trainer_config = ModelTrainerConfig(
            training_pipeline_config
        )

        model_trainer = ModelTrainer(
            model_trainer_config=model_trainer_config,
            data_transformation_artifact=data_transformation_artifact
        )

        model_trainer_artifact = (
            model_trainer.initiate_model_trainer()
        )

        print(model_trainer_artifact)

        logging.info("Model Training Completed")

        # ==========================================
        # STEP 6: MODEL EVALUATION
        # ==========================================

        logging.info("Starting Model Evaluation")

        model_evaluation_config = ModelEvaluationConfig(
            training_pipeline_config
        )

        model_evaluation = ModelEvaluation(
            model_evaluation_config=model_evaluation_config,
            data_transformation_artifact=data_transformation_artifact,
            model_trainer_artifact=model_trainer_artifact
        )

        model_evaluation_artifact = (
            model_evaluation.initiate_model_evaluation()
        )

        print(model_evaluation_artifact)

        logging.info("Model Evaluation Completed")

        # ==========================================
        # PIPELINE COMPLETED
        # ==========================================

        print("\n========== PIPELINE COMPLETED ==========")

        print("Data Ingestion       : SUCCESS")
        print("Data Validation      : SUCCESS")
        print("Data Transformation  : SUCCESS")
        print("Model Training       : SUCCESS")
        print("Model Evaluation     : SUCCESS")

        print("========================================")

    except Exception as e:

        logging.error("Network Security Pipeline Failed")

        raise NetworkSecurityException(e, sys)