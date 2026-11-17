import os
import sys

import certifi
import pymongo
import pandas as pd

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Request
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import (
    JSONResponse,
    FileResponse
)

from fastapi.templating import Jinja2Templates

from uvicorn import run as app_run

from src.exception.exception import NetworkSecurityException

from src.logging.logger import logging

from src.pipeline.training_pipeline import TrainingPipeline

from src.utils.main_utils.utils import load_object

from src.constant.training_pipeline import (
    DATA_INGESTION_COLLECTION_NAME,
    DATA_INGESTION_DATABASE_NAME
)


# ============================================================
# STEP 1: PROJECT CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FINAL_MODEL_DIR = os.path.join(
    BASE_DIR,
    "final_model"
)

MODEL_FILE_PATH = os.path.join(
    FINAL_MODEL_DIR,
    "model.pkl"
)

PREDICTION_OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "prediction_output"
)

TEMPLATE_DIR = os.path.join(
    BASE_DIR,
    "templates"
)

os.makedirs(
    PREDICTION_OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# STEP 2: PREDICTION LABEL CONFIGURATION
# ============================================================

# ASSUMPTION:
# Original dataset: -1 = Phishing, 1 = Legitimate
# Data transformation: -1 becomes 0
#
# Therefore:
# 0 = Phishing
# 1 = Legitimate
#
# Verify this against your original dataset documentation.

PREDICTION_LABELS = {
    0: "Phishing",
    1: "Legitimate"
}


# ============================================================
# STEP 3: ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

mongo_db_url = os.getenv(
    "MONGO_DB_URL"
)

if not mongo_db_url:

    raise ValueError(
        "MONGO_DB_URL is missing from the .env file"
    )

ca = certifi.where()


# ============================================================
# STEP 4: MONGODB CONNECTION
# ============================================================

try:

    client = pymongo.MongoClient(
        mongo_db_url,
        tlsCAFile=ca,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    logging.info(
        "MongoDB connected successfully"
    )

    database = client[
        DATA_INGESTION_DATABASE_NAME
    ]

    collection = database[
        DATA_INGESTION_COLLECTION_NAME
    ]

except Exception as e:

    logging.exception(
        "MongoDB connection failed"
    )

    raise NetworkSecurityException(
        e,
        sys
    )


# ============================================================
# STEP 5: FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Network Security - Phishing Website Detection",
    description="Machine Learning API for detecting phishing websites",
    version="1.0.0"
)


# ============================================================
# STEP 6: CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# STEP 7: HTML TEMPLATE CONFIGURATION
# ============================================================

templates = Jinja2Templates(
    directory=TEMPLATE_DIR
)


# ============================================================
# STEP 8: HOME ROUTE
# ============================================================

@app.get(
    "/",
    tags=["Home"]
)

async def index(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        }
    )


# ============================================================
# STEP 9: HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["Health"]
)

async def health_check():

    return {
        "status": "success",
        "application": "Network Security",
        "message": "API is running successfully"
    }


# ============================================================
# STEP 10: MODEL TRAINING
# ============================================================

@app.get(
    "/train",
    tags=["Training"]
)

async def train_route():

    try:

        logging.info(
            "Starting Network Security training pipeline"
        )

        train_pipeline = TrainingPipeline()

        train_pipeline.run_pipeline()

        logging.info(
            "Model training completed successfully"
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Model training completed successfully"
            }
        )

    except Exception as e:

        logging.exception(
            "Training pipeline failed"
        )

        raise NetworkSecurityException(
            e,
            sys
        )


# ============================================================
# STEP 11: PREDICTION ROUTE
# ============================================================

@app.post(
    "/predict",
    tags=["Prediction"]
)

async def predict_route(
    request: Request,
    file: UploadFile = File(...)
):

    try:

        logging.info(
            "Prediction request received"
        )

        # ----------------------------------------------------
        # STEP 1: VALIDATE FILE
        # ----------------------------------------------------

        if not file.filename:

            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Please select a CSV file"
                }
            )

        if not file.filename.lower().endswith(".csv"):

            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Only CSV files are accepted"
                }
            )

        # ----------------------------------------------------
        # STEP 2: READ CSV
        # ----------------------------------------------------

        try:

            df = pd.read_csv(file.file)

        except Exception:

            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Unable to read CSV file"
                }
            )

        if df.empty:

            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Uploaded CSV file is empty"
                }
            )

        logging.info(
            f"Input dataset shape: {df.shape}"
        )

        # ----------------------------------------------------
        # STEP 3: CHECK MODEL
        # ----------------------------------------------------

        if not os.path.exists(MODEL_FILE_PATH):

            return JSONResponse(
                status_code=404,
                content={
                    "status": "failed",
                    "message": "Trained model not found. Please train the model first."
                }
            )

        # ----------------------------------------------------
        # STEP 4: LOAD TRAINED MODEL
        # ----------------------------------------------------

        network_model = load_object(
            file_path=MODEL_FILE_PATH
        )

        logging.info(
            f"Loaded model type: {type(network_model)}"
        )

        if not hasattr(network_model, "predict"):

            raise TypeError(
                "Loaded model does not contain a predict method"
            )

        # ----------------------------------------------------
        # STEP 5: GENERATE PREDICTIONS
        # ----------------------------------------------------

        y_pred = network_model.predict(df)

        if len(y_pred) != len(df):

            raise ValueError(
                "Number of predictions does not match input records"
            )

        logging.info(
            f"Predictions generated: {len(y_pred)}"
        )

        # ----------------------------------------------------
        # STEP 6: VALIDATE PREDICTION CLASSES
        # ----------------------------------------------------

        prediction_values = [
            int(value) for value in y_pred
        ]

        invalid_predictions = set(
            prediction_values
        ) - set(PREDICTION_LABELS.keys())

        if invalid_predictions:

            raise ValueError(
                f"Unexpected prediction classes: {invalid_predictions}"
            )

        # ----------------------------------------------------
        # STEP 7: ADD PREDICTIONS
        # ----------------------------------------------------

        df["predicted_column"] = prediction_values

        df["prediction_result"] = [
            PREDICTION_LABELS[value]
            for value in prediction_values
        ]

        # ----------------------------------------------------
        # STEP 8: CALCULATE STATISTICS
        # ----------------------------------------------------

        total_records = len(df)

        phishing_count = prediction_values.count(0)

        legitimate_count = prediction_values.count(1)

        phishing_percentage = round(
            (phishing_count / total_records) * 100,
            2
        )

        legitimate_percentage = round(
            (legitimate_count / total_records) * 100,
            2
        )

        logging.info(
            f"Total Records: {total_records}"
        )

        logging.info(
            f"Phishing: {phishing_count}"
        )

        logging.info(
            f"Legitimate: {legitimate_count}"
        )

        # ----------------------------------------------------
        # STEP 9: SAVE PREDICTIONS
        # ----------------------------------------------------

        output_file_path = os.path.join(
            PREDICTION_OUTPUT_DIR,
            "output.csv"
        )

        df.to_csv(
            output_file_path,
            index=False
        )

        logging.info(
            f"Prediction output saved: {output_file_path}"
        )

        # ----------------------------------------------------
        # STEP 10: PREPARE HTML TABLE DATA
        # ----------------------------------------------------

        columns = df.columns.tolist()

        records = df.to_dict(
            orient="records"
        )

        # ----------------------------------------------------
        # STEP 11: RETURN DASHBOARD
        # ----------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="table.html",
            context={

                "request": request,

                "columns": columns,

                "records": records,

                "total_records": total_records,

                "predicted_records": len(y_pred),

                "phishing_count": phishing_count,

                "legitimate_count": legitimate_count,

                "phishing_percentage": phishing_percentage,

                "legitimate_percentage": legitimate_percentage

            }
        )

    except Exception as e:

        logging.exception(
            "Prediction failed"
        )

        raise NetworkSecurityException(
            e,
            sys
        )

    finally:

        await file.close()


# ============================================================
# STEP 12: DOWNLOAD PREDICTION CSV
# ============================================================

@app.get(
    "/download",
    tags=["Prediction"]
)

async def download_predictions():

    output_file_path = os.path.join(
        PREDICTION_OUTPUT_DIR,
        "output.csv"
    )

    if not os.path.exists(output_file_path):

        return JSONResponse(
            status_code=404,
            content={
                "status": "failed",
                "message": "Prediction output not found"
            }
        )

    return FileResponse(
        path=output_file_path,
        filename="phishing_prediction_results.csv",
        media_type="text/csv"
    )


# ============================================================
# STEP 13: APPLICATION EXECUTION
# ============================================================

if __name__ == "__main__":

    app_run(
        app,
        host="0.0.0.0",
        port=8000
    )