import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import mlflow

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    ConfusionMatrixDisplay
)

from src.exception.exception import NetworkSecurityException
from src.logging.logger import logging

from src.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact
)

from src.entity.config_entity import ModelEvaluationConfig

from src.utils.main_utils.utils import (
    load_object,
    load_numpy_array_data
)


class ModelEvaluation:

    def __init__(
        self,
        model_evaluation_config: ModelEvaluationConfig,
        data_transformation_artifact: DataTransformationArtifact,
        model_trainer_artifact: ModelTrainerArtifact
    ):

        try:
            self.model_evaluation_config = model_evaluation_config
            self.data_transformation_artifact = data_transformation_artifact
            self.model_trainer_artifact = model_trainer_artifact

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:

        try:

            logging.info("Starting Model Evaluation")

            # ==========================================
            # STEP 1: LOAD TRAINED MODEL
            # ==========================================

            trained_model = load_object(
                file_path=self.model_trainer_artifact.trained_model_file_path
            )

            model = trained_model.model

            # ==========================================
            # STEP 2: LOAD TEST DATA
            # ==========================================

            test_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_test_file_path
            )

            X_test = test_arr[:, :-1]
            y_test = test_arr[:, -1]

            # ==========================================
            # STEP 3: PREDICTIONS
            # ==========================================

            y_pred = model.predict(X_test)

            # ==========================================
            # STEP 4: EVALUATION METRICS
            # ==========================================

            accuracy = accuracy_score(y_test, y_pred)

            precision = precision_score(
                y_test,
                y_pred,
                average="weighted",
                zero_division=0
            )

            recall = recall_score(
                y_test,
                y_pred,
                average="weighted",
                zero_division=0
            )

            f1 = f1_score(
                y_test,
                y_pred,
                average="weighted",
                zero_division=0
            )

            # ==========================================
            # STEP 5: ROC AUC
            # ==========================================

            roc_auc = None

            if hasattr(model, "predict_proba") and len(np.unique(y_test)) == 2:

                y_probability = model.predict_proba(X_test)[:, 1]

                roc_auc = roc_auc_score(
                    y_test,
                    y_probability
                )

            # ==========================================
            # STEP 6: CLASSIFICATION REPORT
            # ==========================================

            report = classification_report(
                y_test,
                y_pred,
                output_dict=True,
                zero_division=0
            )

            # ==========================================
            # STEP 7: CONFUSION MATRIX
            # ==========================================

            cm = confusion_matrix(y_test, y_pred)

            # ==========================================
            # STEP 8: CREATE OUTPUT DIRECTORY
            # ==========================================

            os.makedirs(
                self.model_evaluation_config.model_evaluation_dir,
                exist_ok=True
            )

            # ==========================================
            # STEP 9: SAVE EVALUATION REPORT
            # ==========================================

            evaluation_report = {
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "roc_auc": (
                    float(roc_auc) if roc_auc is not None else None
                ),
                "classification_report": report,
                "confusion_matrix": cm.tolist()
            }

            with open(
                self.model_evaluation_config.evaluation_report_file_path,
                "w"
            ) as file:

                json.dump(
                    evaluation_report,
                    file,
                    indent=4
                )

            # ==========================================
            # STEP 10: SAVE CONFUSION MATRIX IMAGE
            # ==========================================

            display = ConfusionMatrixDisplay(
                confusion_matrix=cm
            )

            display.plot()

            plt.title("Network Security Model - Confusion Matrix")
            plt.tight_layout()

            plt.savefig(
                self.model_evaluation_config.confusion_matrix_image_path
            )

            plt.close()

            # ==========================================
            # STEP 11: MLFLOW TRACKING
            # ==========================================

            logging.info("Logging evaluation results to MLflow")

            with mlflow.start_run(run_name="Model_Evaluation"):

                # Log model information
                mlflow.log_param(
                    "model_type",
                    type(model).__name__
                )

                mlflow.log_param(
                    "evaluation_dataset",
                    "test"
                )

                # Log evaluation metrics
                mlflow.log_metric(
                    "accuracy",
                    float(accuracy)
                )

                mlflow.log_metric(
                    "precision",
                    float(precision)
                )

                mlflow.log_metric(
                    "recall",
                    float(recall)
                )

                mlflow.log_metric(
                    "f1_score",
                    float(f1)
                )

                if roc_auc is not None:

                    mlflow.log_metric(
                        "roc_auc",
                        float(roc_auc)
                    )

                # Log evaluation report
                mlflow.log_artifact(
                    self.model_evaluation_config.evaluation_report_file_path,
                    artifact_path="evaluation"
                )

                # Log confusion matrix
                mlflow.log_artifact(
                    self.model_evaluation_config.confusion_matrix_image_path,
                    artifact_path="evaluation"
                )

                logging.info(
                    "Evaluation metrics and artifacts logged successfully"
                )

            # ==========================================
            # STEP 12: PRINT RESULTS
            # ==========================================

            print("\n========== MODEL EVALUATION ==========")

            print(f"Accuracy  : {accuracy:.4f}")
            print(f"Precision : {precision:.4f}")
            print(f"Recall    : {recall:.4f}")
            print(f"F1 Score  : {f1:.4f}")

            if roc_auc is not None:
                print(f"ROC-AUC   : {roc_auc:.4f}")
            else:
                print("ROC-AUC   : Not available")

            print("\nClassification Report:")

            print(
                classification_report(
                    y_test,
                    y_pred,
                    zero_division=0
                )
            )

            print("Confusion Matrix:")
            print(cm)

            print("======================================")

            # ==========================================
            # STEP 13: MODEL ACCEPTANCE
            # ==========================================

            # Placeholder only.
            # A genuine acceptance threshold must be configured.

            is_model_accepted = True

            # ==========================================
            # STEP 14: CREATE EVALUATION ARTIFACT
            # ==========================================

            model_evaluation_artifact = ModelEvaluationArtifact(

                is_model_accepted=is_model_accepted,

                evaluation_report_file_path=(
                    self.model_evaluation_config.evaluation_report_file_path
                ),

                confusion_matrix_image_path=(
                    self.model_evaluation_config.confusion_matrix_image_path
                ),

                accuracy=float(accuracy),

                precision=float(precision),

                recall=float(recall),

                f1_score=float(f1),

                roc_auc=(
                    float(roc_auc) if roc_auc is not None else 0.0
                )
            )

            logging.info(
                f"Model Evaluation Artifact: {model_evaluation_artifact}"
            )

            return model_evaluation_artifact

        except Exception as e:

            raise NetworkSecurityException(e, sys)