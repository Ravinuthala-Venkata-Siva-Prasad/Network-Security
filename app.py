import os
import sys
import secrets

import certifi
import pymongo
import pandas as pd

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    Request,
    Header,
    HTTPException
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


PREDICTION_LABELS = {
    0: "Phishing",
    1: "Legitimate"
}


load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

MONGO_DB_URL = os.getenv(
    "MONGO_DB_URL"
)

TRAINING_API_KEY = os.getenv(
    "TRAINING_API_KEY"
)

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    ""
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in CORS_ORIGINS.split(",")
    if origin.strip()
]

if not MONGO_DB_URL:

    raise ValueError(
        "MONGO_DB_URL is missing from environment variables"
    )


try:

    ca = certifi.where()

    client = pymongo.MongoClient(
        MONGO_DB_URL,
        tlsCAFile=ca,
        serverSelectionTimeoutMS=5000
    )

    # Verify MongoDB connection

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

app = FastAPI(

    title="Network Security - Phishing Website Detection",

    description=(
        "Machine Learning API for detecting "
        "phishing websites using a trained ML model."
    ),

    version="2.0.0"
)


app.add_middleware(

    CORSMiddleware,

    allow_origins=ALLOWED_ORIGINS,

    allow_credentials=False,

    allow_methods=[
        "GET",
        "POST"
    ],

    allow_headers=[
        "Content-Type",
        "Authorization"
    ]

)


templates = Jinja2Templates(

    directory=TEMPLATE_DIR

)


@app.get(
    "/",
    tags=["Home"]
)

async def index(
    request: Request
):

    return templates.TemplateResponse(

        request=request,

        name="index.html",

        context={
            "request": request
        }

    )


@app.get(
    "/health",
    tags=["Health"]
)

async def health_check():

    return {

        "status": "success",

        "application": "Network Security",

        "message": "API is running successfully",

        "model_available": os.path.exists(
            MODEL_FILE_PATH
        )

    }


@app.post(
    "/train",
    tags=["Training"]
)

async def train_route(

    x_training_key: str | None = Header(
        default=None
    )

):


    if not TRAINING_API_KEY:

        raise HTTPException(

            status_code=503,

            detail="Training endpoint is disabled"

        )

    if not x_training_key or not secrets.compare_digest(

        x_training_key,

        TRAINING_API_KEY

    ):

        raise HTTPException(

            status_code=401,

            detail="Unauthorized training request"

        )

   
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

                "message": (
                    "Model training completed successfully"
                )

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

        if not file.filename:

            raise HTTPException(

                status_code=400,

                detail="Please select a CSV file"

            )

        if not file.filename.lower().endswith(".csv"):

            raise HTTPException(

                status_code=400,

                detail="Only CSV files are accepted"

            )

        try:

            df = pd.read_csv(
                file.file
            )

        except Exception as e:

            logging.exception(
                "Unable to read uploaded CSV"
            )

            raise HTTPException(

                status_code=400,

                detail="Unable to read CSV file"

            )

        if df.empty:

            raise HTTPException(

                status_code=400,

                detail="Uploaded CSV file is empty"

            )

        logging.info(
            f"Input dataset shape: {df.shape}"
        )

       
        if not os.path.exists(MODEL_FILE_PATH):

            raise HTTPException(

                status_code=404,

                detail=(
                    "Trained model not found. "
                    "Please deploy the trained model first."
                )

            )

        network_model = load_object(

            file_path=MODEL_FILE_PATH

        )

        logging.info(
            f"Loaded model type: {type(network_model)}"
        )

        if not hasattr(
            network_model,
            "predict"
        ):

            raise TypeError(
                "Loaded model does not contain a predict method"
            )

       
        y_pred = network_model.predict(
            df
        )

        if len(y_pred) != len(df):

            raise ValueError(
                "Number of predictions does not match input records"
            )

        logging.info(
            f"Predictions generated: {len(y_pred)}"
        )

        prediction_values = [

            int(value)

            for value in y_pred

        ]

        invalid_predictions = (

            set(prediction_values)

            -

            set(PREDICTION_LABELS.keys())

        )

        if invalid_predictions:

            raise ValueError(

                f"Unexpected prediction classes: "
                f"{invalid_predictions}"

            )

        df["predicted_column"] = prediction_values

        df["prediction_result"] = [

            PREDICTION_LABELS[value]

            for value in prediction_values

        ]

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

        columns = df.columns.tolist()

        records = df.to_dict(
            orient="records"
        )
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

    except HTTPException:

        raise

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

        raise HTTPException(

            status_code=404,

            detail="Prediction output not found"

        )

    return FileResponse(

        path=output_file_path,

        filename="phishing_prediction_results.csv",

        media_type="text/csv"

    )

if __name__ == "__main__":

    app_run(

        app,

        host="0.0.0.0",

        port=8000,

        reload=False

    )