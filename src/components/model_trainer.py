import os
import sys

from src.exception.exception import NetworkSecurityException
from src.logging.logger import logging

from src.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact
)

from src.entity.config_entity import ModelTrainerConfig

from src.utils.ml_utils.model.estimator import NetworkModel

from src.utils.main_utils.utils import (
    save_object,
    load_object,
    load_numpy_array_data,
    evaluate_models
)

from src.utils.ml_utils.metric.classification_metric import (
    get_classification_score
)

from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier
)

import mlflow
import dagshub
dagshub.init(repo_owner='Ravinuthala-Venkata-Siva-Prasad', repo_name='Network-Security', mlflow=True)


class ModelTrainer:

    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact
    ):

        try:

            self.model_trainer_config = model_trainer_config

            self.data_transformation_artifact = (
                data_transformation_artifact
            )

        except Exception as e:

            raise NetworkSecurityException(e, sys)

    def track_mlflow(self, best_model, classification_metric):

        try:

            with mlflow.start_run():

                # Classification Metrics
                f1_score = classification_metric.f1_score

                precision_score = (
                    classification_metric.precision_score
                )

                recall_score = (
                    classification_metric.recall_score
                )

                # Log Metrics
                mlflow.log_metric(
                    "f1_score",
                    f1_score
                )

                mlflow.log_metric(
                    "precision",
                    precision_score
                )

                mlflow.log_metric(
                    "recall_score",
                    recall_score
                )

                # Log Model
                mlflow.sklearn.log_model(
                    sk_model=best_model,
                    name="model",
                    skops_trusted_types=[
                        "sklearn.tree._tree.Tree"
                    ]
                )

                logging.info(
                    "Model and classification metrics logged successfully"
                )

        except Exception as e:

            raise NetworkSecurityException(e, sys)

    def train_model(
        self,
        X_train,
        y_train,
        X_test,
        y_test
    ):

        try:

            logging.info("Starting model training")
            models = {

                "Random Forest": RandomForestClassifier(
                    random_state=42,
                    verbose=1
                ),

                "Decision Tree": DecisionTreeClassifier(
                    random_state=42
                ),

                "Gradient Boosting": GradientBoostingClassifier(
                    random_state=42,
                    verbose=1
                ),

                "Logistic Regression": LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    verbose=1
                ),

                "AdaBoost": AdaBoostClassifier(
                    random_state=42
                )

            }
            params = {

                "Decision Tree": {

                    "criterion": [
                        "gini",
                        "entropy",
                        "log_loss"
                    ]

                },

                "Random Forest": {

                    "n_estimators": [
                        8,
                        16,
                        32,
                        128,
                        256
                    ]

                },

                "Gradient Boosting": {

                    "learning_rate": [
                        0.1,
                        0.01,
                        0.05,
                        0.001
                    ],

                    "subsample": [
                        0.6,
                        0.7,
                        0.75,
                        0.85,
                        0.9
                    ],

                    "n_estimators": [
                        8,
                        16,
                        32,
                        64,
                        128,
                        256
                    ]

                },

                "Logistic Regression": {},

                "AdaBoost": {

                    "learning_rate": [
                        0.1,
                        0.01,
                        0.001
                    ],

                    "n_estimators": [
                        8,
                        16,
                        32,
                        64,
                        128,
                        256
                    ]

                }

            }

            logging.info("Evaluating different ML models")

            model_report = evaluate_models(

                X_train=X_train,

                y_train=y_train,

                X_test=X_test,

                y_test=y_test,

                models=models,

                param=params

            )

            logging.info(
                f"Model Evaluation Report: {model_report}"
            )

            best_model_score = max(
                model_report.values()
            )

            best_model_name = list(model_report.keys())[
                list(model_report.values()).index(
                    best_model_score
                )
            ]

            best_model = models[best_model_name]

            logging.info(
                f"Best Model: {best_model_name}"
            )

            logging.info(
                f"Best Model Score: {best_model_score}"
            )

            print("\n========== BEST MODEL ==========")

            print("Model Name:", best_model_name)

            print("Model Score:", best_model_score)

            print("================================")

            y_train_pred = best_model.predict(X_train)

            classification_train_metric = (
                get_classification_score(

                    y_true=y_train,

                    y_pred=y_train_pred

                )
            )

            logging.info(
                f"Training Metrics: {classification_train_metric}"
            )

            y_test_pred = best_model.predict(X_test)

            classification_test_metric = (
                get_classification_score(

                    y_true=y_test,

                    y_pred=y_test_pred

                )
            )

            logging.info(
                f"Testing Metrics: {classification_test_metric}"
            )

            logging.info("Tracking training metrics with MLflow")

            self.track_mlflow(
                best_model,
                classification_train_metric
            )

            self.track_mlflow(
                best_model,
                classification_test_metric
            )

            preprocessor = load_object(

                file_path=(
                    self.data_transformation_artifact
                    .transformed_object_file_path
                )

            )

            model_dir_path = os.path.dirname(
                self.model_trainer_config.trained_model_file_path
            )

            os.makedirs(
                model_dir_path,
                exist_ok=True
            )

            network_model = NetworkModel(

                preprocessor=preprocessor,

                model=best_model

            )
            save_object(

                self.model_trainer_config.trained_model_file_path,

                obj=network_model

            )
            os.makedirs(
                "final_model",
                exist_ok=True
            )

            save_object(

                "final_model/model.pkl",

                obj=network_model

            )

            logging.info(
                "Trained model saved successfully"
            )

            model_trainer_artifact = ModelTrainerArtifact(

                trained_model_file_path=(
                    self.model_trainer_config.trained_model_file_path
                ),

                train_metric_artifact=(
                    classification_train_metric
                ),

                test_metric_artifact=(
                    classification_test_metric
                )

            )

            logging.info(
                f"Model Trainer Artifact: {model_trainer_artifact}"
            )

            print("\n========== MODEL TRAINING COMPLETED ==========")

            print("Best Model:", best_model_name)

            print("Best Model Score:", best_model_score)

            print(
                "Training F1 Score:",
                classification_train_metric.f1_score
            )

            print(
                "Testing F1 Score:",
                classification_test_metric.f1_score
            )

            print(
                "Model Saved:",
                self.model_trainer_config.trained_model_file_path
            )

            print("==============================================")

            return model_trainer_artifact

        except Exception as e:

            raise NetworkSecurityException(e, sys)

    def initiate_model_trainer(self) -> ModelTrainerArtifact:

        try:

            logging.info(
                "Entered initiate_model_trainer method"
            )

            train_file_path = (
                self.data_transformation_artifact
                .transformed_train_file_path
            )

            test_file_path = (
                self.data_transformation_artifact
                .transformed_test_file_path
            )
            train_arr = load_numpy_array_data(
                train_file_path
            )

            test_arr = load_numpy_array_data(
                test_file_path
            )

            logging.info(
                f"Training Array Shape: {train_arr.shape}"
            )

            logging.info(
                f"Testing Array Shape: {test_arr.shape}"
            )

            X_train = train_arr[:, :-1]

            y_train = train_arr[:, -1]

            X_test = test_arr[:, :-1]

            y_test = test_arr[:, -1]

         

            model_trainer_artifact = self.train_model(

                X_train,

                y_train,

                X_test,

                y_test

            )

            logging.info(
                "Model training completed successfully"
            )

            return model_trainer_artifact

        except Exception as e:

            raise NetworkSecurityException(e, sys)