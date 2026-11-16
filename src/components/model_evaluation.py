import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt

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

            # Step 1: Load trained model
            trained_model = load_object(
                file_path=self.model_trainer_artifact.trained_model_file_path
            )

            # The saved object is a NetworkModel wrapper.
            # Access its underlying sklearn estimator.
            model = trained_model.model

            # Step 2: Load transformed testing data
            test_arr = load_numpy_array_data(
                self.data_transformation_artifact.transformed_test_file_path
            )

            X_test = test_arr[:, :-1]
            y_test = test_arr[:, -1]

            # Step 3: Generate predictions
            y_pred = model.predict(X_test)

            # Step 4: Calculate evaluation metrics
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

            # Step 5: Calculate ROC-AUC
            roc_auc = None

            if hasattr(model, "predict_proba") and len(np.unique(y_test)) == 2:

                y_probability = model.predict_proba(X_test)[:, 1]

                roc_auc = roc_auc_score(
                    y_test,
                    y_probability
                )

            # Step 6: Classification report
            report = classification_report(
                y_test,
                y_pred,
                output_dict=True,
                zero_division=0
            )

            # Step 7: Confusion matrix
            cm = confusion_matrix(y_test, y_pred)

            # Step 8: Create output directory
            os.makedirs(
                self.model_evaluation_config.model_evaluation_dir,
                exist_ok=True
            )

            # Step 9: Save evaluation report
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

            # Step 10: Save confusion matrix image
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

            # Step 11: Print results
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
            print(classification_report(
                y_test,
                y_pred,
                zero_division=0
            ))

            print("Confusion Matrix:")
            print(cm)

            print("======================================")

            # Step 12: Model acceptance
            # This is a preliminary acceptance check.
            # We will define a production threshold separately.
            is_model_accepted = True

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