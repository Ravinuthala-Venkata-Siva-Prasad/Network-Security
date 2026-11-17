# app.py

import os
import sys
import certifi
import pymongo
import pandas as pd

from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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
# 1. PROJECT CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FINAL_MODEL_DIR = os.path.join(BASE_DIR, "final_model")

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

os.makedirs(PREDICTION_OUTPUT_DIR, exist_ok=True)


# ============================================================
# 2. ENVIRONMENT CONFIGURATION
# ============================================================

load_dotenv(
    dotenv_path=os.path.join(BASE_DIR, ".env"),
    override=False
)

mongo_db_url = os.getenv("MONGO_DB_URL", "").strip()

# Remove optional surrounding quotation marks
if (
    len(mongo_db_url) >= 2
    and mongo_db_url[0] == mongo_db_url[-1]
    and mongo_db_url[0] in ("'", '"')
):
    mongo_db_url = mongo_db_url[1:-1].strip()

if not mongo_db_url:
    raise ValueError(
        "MONGO_DB_URL environment variable is missing."
    )

if not mongo_db_url.startswith(
    ("mongodb://", "mongodb+srv://")
):
    raise ValueError(
        "Invalid MongoDB URI. "
        "Expected mongodb:// or mongodb+srv://"
    )

if "YOUR_" in mongo_db_url:
    raise ValueError(
        "MongoDB URI contains placeholder credentials."
    )

ca = certifi.where()


# ============================================================
# 3. MONGODB CONNECTION
# ============================================================

client = None

try:

    logging.info("Connecting to MongoDB...")

    client = pymongo.MongoClient(
        mongo_db_url,
        tlsCAFile=ca,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )

    client.admin.command("ping")

    logging.info("MongoDB connected successfully.")

    print("MongoDB connected successfully!")

    database = client[DATA_INGESTION_DATABASE_NAME]

    collection = database[
        DATA_INGESTION_COLLECTION_NAME
    ]

except Exception as e:

    logging.exception("MongoDB connection failed.")

    if client is not None:
        client.close()

    raise NetworkSecurityException(e, sys)


# ============================================================
# 4. FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Network Security - Phishing Website Detection",
    description="Machine Learning API for Phishing Website Detection",
    version="1.0.0"
)


# ============================================================
# 5. CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# 6. HTML TEMPLATE CONFIGURATION
# ============================================================

templates = Jinja2Templates(
    directory=TEMPLATE_DIR
)


# ============================================================
# 7. HOME ROUTE
# ============================================================

@app.get("/", tags=["Home"])
async def index(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        }
    )


# ============================================================
# 8. HEALTH CHECK
# ============================================================

@app.get("/health", tags=["Health"])
async def health_check():

    return {
        "status": "success",
        "application": "Network Security",
        "message": "API is running successfully"
    }


# ============================================================
# 9. MODEL TRAINING
# ============================================================

@app.get("/train", tags=["Training"])
async def train_route():

    try:

        logging.info("Starting training pipeline.")

        train_pipeline = TrainingPipeline()

        train_pipeline.run_pipeline()

        return {
            "status": "success",
            "message": "Model training completed successfully"
        }

    except Exception as e:

        logging.exception("Training pipeline failed.")

        raise NetworkSecurityException(e, sys)


# ============================================================
# 10. PREDICTION
# ============================================================

@app.post("/predict", tags=["Prediction"])
async def predict_route(
    request: Request,
    file: UploadFile = File(...)
):

    try:

        # Validate filename
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Please select a CSV file"
                }
            )

        # Validate CSV extension
        if not file.filename.lower().endswith(".csv"):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Only CSV files are accepted"
                }
            )

        # Read CSV
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

        logging.info(f"Input dataset shape: {df.shape}")

        # Check model
        if not os.path.exists(MODEL_FILE_PATH):
            return JSONResponse(
                status_code=404,
                content={
                    "status": "failed",
                    "message": "Trained model not found"
                }
            )

        # Load model
        network_model = load_object(
            file_path=MODEL_FILE_PATH
        )

        # Generate predictions
        y_pred = network_model.predict(df)

        if len(y_pred) != len(df):
            raise ValueError(
                "Prediction count does not match input rows."
            )

        # Convert predictions
        prediction_values = [
            int(value) for value in y_pred
        ]

        # Prediction mapping
        prediction_labels = {
            0: "Phishing",
            1: "Legitimate"
        }

        invalid_predictions = (
            set(prediction_values)
            - set(prediction_labels.keys())
        )

        if invalid_predictions:
            raise ValueError(
                f"Unexpected prediction classes: {invalid_predictions}"
            )

        # Add predictions
        df["predicted_column"] = prediction_values

        df["prediction_result"] = [
            prediction_labels[value]
            for value in prediction_values
        ]

        # Statistics
        total_records = len(df)

        phishing_count = prediction_values.count(0)

        legitimate_count = prediction_values.count(1)

        phishing_percentage = round(
            phishing_count / total_records * 100,
            2
        )

        legitimate_percentage = round(
            legitimate_count / total_records * 100,
            2
        )

        # Save results
        output_file_path = os.path.join(
            PREDICTION_OUTPUT_DIR,
            "output.csv"
        )

        df.to_csv(
            output_file_path,
            index=False
        )

        # Prepare HTML data
        columns = df.columns.tolist()

        records = df.to_dict(orient="records")

        # Return results
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

        logging.exception("Prediction failed.")

        raise NetworkSecurityException(e, sys)

    finally:

        await file.close()


# ============================================================
# 11. DOWNLOAD PREDICTION RESULTS
# ============================================================

@app.get("/download", tags=["Prediction"])
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
# 12. APPLICATION SHUTDOWN
# ============================================================

@app.on_event("shutdown")
def shutdown_event():

    if client is not None:
        client.close()
        logging.info("MongoDB connection closed.")


# ============================================================
# 13. APPLICATION EXECUTION
# ============================================================

if __name__ == "__main__":

    app_run(
        app,
        host="0.0.0.0",
        port=8000
    )