# Network Security – Phishing Website Detection using Machine Learning & AWS CI/CD

An end-to-end Machine Learning application designed to detect phishing websites using a Random Forest classifier. This project integrates FastAPI, MongoDB Atlas, Docker, AWS EC2, Amazon ECR, and GitHub Actions to automate application deployment through a CI/CD pipeline.

---

## Project Overview

Phishing websites are malicious websites designed to imitate legitimate websites to steal sensitive information such as login credentials, personal information, and financial details.

This project uses Machine Learning to analyze website-related features and classify websites into two categories:

- **Phishing:** Potentially malicious website.
- **Legitimate:** Website classified as legitimate by the trained model.

The trained Random Forest model is integrated into a FastAPI application and deployed on AWS EC2 using Docker and GitHub Actions.

---

## Key Features

- Phishing website detection using Machine Learning.
- Random Forest classification algorithm.
- Dataset containing 11,055 records and 30 input features.
- Automated data ingestion and preprocessing.
- Model training and prediction.
- FastAPI-based web application.
- CSV-based batch predictions.
- MongoDB Atlas integration.
- Docker containerization.
- AWS EC2 deployment.
- Amazon ECR for Docker image storage.
- GitHub Actions CI/CD automation.
- Application health-check endpoint.

---

## Dataset Information

The model was trained using a phishing website dataset.

| Dataset Attribute | Value |
|---|---:|
| Total Records | 11,055 |
| Input Features | 30 |
| Target Variable | 1 |
| Total Columns | 31 |
| Target Column | Result |
| Machine Learning Algorithm | Random Forest |
| Problem Type | Binary Classification |

**Important:** 11,055 represents the number of records (rows), not the number of input features.

The model uses 30 input features to predict whether a website is phishing or legitimate.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Machine Learning | Scikit-learn |
| ML Algorithm | Random Forest |
| Data Processing | Pandas, NumPy |
| Backend Framework | FastAPI |
| Database | MongoDB Atlas |
| Model Serialization | Pickle |
| API Server | Uvicorn |
| Containerization | Docker |
| Cloud Platform | AWS |
| Container Registry | Amazon ECR |
| Cloud Deployment | Amazon EC2 |
| CI/CD | GitHub Actions |
| Version Control | Git, GitHub |

---

## System Architecture

The following diagram represents the overall application workflow.

```mermaid
flowchart TD
    A[User] --> B[FastAPI Web Application]
    B --> C[Upload CSV Dataset]
    C --> D[Data Preprocessing]
    D --> E[Trained Random Forest Model]
    E --> F{Prediction}
    F --> G[Phishing Website]
    F --> H[Legitimate Website]
    G --> I[Display Prediction Results]
    H --> I
    I --> J[Download Prediction CSV]
```

---

## Machine Learning Workflow

The project follows an end-to-end Machine Learning pipeline.

1. Dataset collection.
2. Data ingestion.
3. Data validation.
4. Data transformation.
5. Feature preparation.
6. Random Forest model training.
7. Model evaluation.
8. Model serialization.
9. Prediction using the trained model.

### Model Information

**Algorithm:** Random Forest Classifier

Random Forest is an ensemble learning algorithm that combines multiple decision trees to perform classification.

The trained model analyzes 30 input features and generates a binary classification prediction.

---

## Application Screenshots

### 1. Application Home Page

The home page allows users to upload a CSV dataset containing the required 30 input features.

![Application Home Page](docs/images/home-page.png)

### 2. Prediction Results

The application processes the uploaded dataset and generates phishing website predictions.

![Prediction Results](docs/images/prediction-results.png)

### 3. FastAPI Swagger Documentation

Swagger UI provides interactive API documentation for testing the available application endpoints.

![FastAPI Swagger Documentation](docs/images/swagger-api.png)

### 4. GitHub Actions CI/CD Pipeline

GitHub Actions automates the Docker build and deployment workflow.

![GitHub Actions CI/CD Pipeline](docs/images/github-actions-deployment.png)

### 5. AWS EC2 Deployment

The application is deployed and hosted on an AWS EC2 instance.

![AWS EC2 Deployment](docs/images/aws-ec2-deployment.png)

---

## Application API Endpoints

The FastAPI application provides the following endpoints.

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Application home page |
| `/health` | GET | Application health check |
| `/docs` | GET | Swagger API documentation |
| `/train` | GET | Training route |
| `/predict` | POST | Upload CSV and generate predictions |
| `/download` | GET | Download prediction results |

### Health Check

The health endpoint checks whether the FastAPI application is running.

Example:

```http
GET /health
```

Example response:

```json
{
    "status": "success",
    "application": "Network Security",
    "message": "API is running successfully"
}
```

---

## Cloud Deployment Architecture

The project uses AWS services to deploy the Machine Learning application.

```mermaid
flowchart TD
    A[Developer] --> B[GitHub Repository]
    B --> C[GitHub Actions]
    C --> D[Self-Hosted Runner]
    D --> E[Docker Build]
    E --> F[Amazon ECR]
    F --> G[AWS EC2]
    G --> H[Docker Container]
    H --> I[FastAPI Application]
    I --> J[Health Check]
    J --> K[Application Available]
```

### AWS Services Used

| AWS Service | Purpose |
|---|---|
| Amazon EC2 | Hosting the application |
| Amazon ECR | Storing Docker images |
| IAM Role | AWS permissions and access |
| Security Groups | Managing inbound and outbound network access |

---

## CI/CD Pipeline

GitHub Actions automates the application deployment process.

### Deployment Workflow

1. Developer pushes code to GitHub.
2. GitHub Actions triggers the deployment workflow.
3. The self-hosted runner checks out the repository.
4. Python dependencies and project files are verified.
5. Docker image is built.
6. Docker image is pushed to Amazon ECR.
7. EC2 pulls the latest Docker image.
8. The existing application container is replaced.
9. The new Docker container starts.
10. Health check verifies application availability.

### CI/CD Deployment Flow

```mermaid
flowchart TD
    A[Code Push] --> B[GitHub Actions Trigger]
    B --> C[Checkout Repository]
    C --> D[Verify Environment]
    D --> E[Verify Model File]
    E --> F[Docker Build]
    F --> G[Login to Amazon ECR]
    G --> H[Push Docker Image]
    H --> I[Pull Latest Image on EC2]
    I --> J[Replace Existing Container]
    J --> K[Start New Container]
    K --> L[Application Health Check]
    L --> M[Deployment Successful]
```

---

## Run the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Ravinuthala-Venkata-Siva-Prasad/Network-Security-Phishing-Website-Detection-using-Machine-Learning-AWS-CI-CD.git
```

### 2. Navigate to the Project Directory

```bash
cd Network-Security-Phishing-Website-Detection-using-Machine-Learning-AWS-CI-CD
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Environment Variables

Create a `.env` file in the project root directory.

```env
MONGO_DB_URL=your_mongodb_connection_string
ENABLE_DAGSHUB_TRACKING=false
```

Use your own MongoDB connection string.

**Security:** Never upload database passwords, API tokens, AWS credentials, or `.env` files to GitHub.

### 7. Start the Application

```bash
python app.py
```

### 8. Access the Application

Home Page:

```text
http://127.0.0.1:8000/
```

Swagger Documentation:

```text
http://127.0.0.1:8000/docs
```

Health Check:

```text
http://127.0.0.1:8000/health
```

---

## Docker Deployment

### 1. Build Docker Image

```bash
docker build -t network-security .
```

### 2. Run Docker Container

```bash
docker run -d \
  --name network-security-container \
  -p 8000:8000 \
  --env-file .env \
  network-security
```

### 3. Check Running Containers

```bash
docker ps
```

### 4. View Container Logs

```bash
docker logs network-security-container
```

---

## AWS Deployment

The application is deployed using:

- AWS EC2
- Amazon ECR
- IAM Role
- Docker
- GitHub Actions

### Deployment Process

1. Configure an EC2 instance.
2. Install Docker and AWS CLI.
3. Configure the required IAM role and ECR permissions.
4. Create an Amazon ECR repository.
5. Configure the GitHub Actions self-hosted runner.
6. Configure the deployment workflow.
7. Build and push the Docker image to ECR.
8. Pull the image from ECR on EC2.
9. Run the Docker container.
10. Verify the application using the health endpoint.

---

## Project Structure

The following is an illustrative project structure. Adjust it to match the actual files in your repository.

```text
Network-Security/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── README.md
│
├── final_model/
│   └── model.pkl
│
├── prediction_output/
│
├── templates/
│   ├── index.html
│   └── table.html
│
├── src/
│   ├── components/
│   ├── pipeline/
│   ├── constant/
│   └── utils/
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
└── docs/
    └── images/
        ├── home-page.png
        ├── prediction-results.png
        ├── swagger-api.png
        ├── github-actions-deployment.png
        └── aws-ec2-deployment.png
```

---

## Learning Outcomes

Through this project, I gained practical experience in:

- End-to-end Machine Learning development.
- Data preprocessing and model training.
- Binary classification using Random Forest.
- Building APIs using FastAPI.
- MongoDB Atlas integration.
- Docker image creation and container management.
- AWS EC2 and Amazon ECR deployment.
- GitHub Actions CI/CD automation.
- Deploying and maintaining a Machine Learning application.

---

## Future Improvements

- Improve model performance through hyperparameter tuning.
- Compare additional classification algorithms.
- Add model monitoring and logging.
- Implement HTTPS with a custom domain.
- Improve application security and authentication.
- Add real-time website URL analysis.
- Integrate additional threat intelligence sources.

---

## Author

**Ravinuthala Venkata Siva Prasad**

M.Tech – Computer Science and Engineering (Artificial Intelligence)

GitHub: [Network Security – Phishing Website Detection](https://github.com/Ravinuthala-Venkata-Siva-Prasad/Network-Security-Phishing-Website-Detection-using-Machine-Learning-AWS-CI-CD)

LinkedIn: [LinkedIn Profile](https://www.linkedin.com/in/ravinuthala-venkata-siva-prasad/)

---

## License

This project is intended for educational and research purposes.

Add a LICENSE file to the repository if you want to distribute it under a specific open-source license.
