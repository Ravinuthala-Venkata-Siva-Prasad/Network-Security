import sys
import pandas as pd

from src.exception.exception import NetworkSecurityException
from src.logging.logger import logging


class NetworkModel:

    def __init__(self, preprocessor, model):
        try:
            self.preprocessor = preprocessor
            self.model = model

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def predict(self, x):

        try:
            logging.info("Starting prediction")

            # Ensure input is a DataFrame
            if not isinstance(x, pd.DataFrame):
                x = pd.DataFrame(x)

            # Apply preprocessing
            x_transform = self.preprocessor.transform(x)

            logging.info(
                f"Preprocessed input shape: {x_transform.shape}"
            )

            # Generate predictions
            y_hat = self.model.predict(x_transform)

            logging.info("Prediction completed successfully")

            return y_hat

        except Exception as e:
            raise NetworkSecurityException(e, sys)