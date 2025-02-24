# AWS CDK REST API with Cognito, Python Lambda, and GitHub Actions CI

## Overview
This project uses AWS CDK in TypeScript to create a REST API secured with Cognito. It connects to a Python Lambda function that interacts with a MongoDB database (mocked with `mongomock` for testing) and integrates with AWS services like Kinesis, SNS, and CloudWatch. A CI pipeline is set up using GitHub Actions to run unit tests.

## Features
- **Cognito Authentication** for API security
- **Reject requests without a valid Bearer token** (any non-empty string is acceptable)
- **Python Lambda** with MongoEngine for data persistence
- CRUD operations for `Item` management:
  - `POST /items`: Create a new item with validation
  - `GET /items`: List all items
  - `GET /items/{id}`: Get a specific item by ID
  - `PATCH /items/{id}`: Update item details
  - `DELETE /items/{id}`: Remove an item
- **Kinesis Stream** for real-time data logging
- **Stream logs to [Grafana](http://samplepy.grafana.net/)**
- **SNS** integration for notifications
- **CloudWatch Logs** for monitoring
- **GitHub Actions CI Pipeline** for automated testing

## Microservices Design Approach
This API is built using a microservices architecture with the following key principles:

1. **Separation of Concerns**
   - **Authentication Service:** Managed by AWS Cognito.
   - **Item Management Service:** Implemented using a dedicated Lambda function for CRUD operations.
   - **Logging Service:** Real-time logs sent to Kinesis and visualized in Grafana.
   - **Notification Service:** Event-driven notifications using SNS.

2. **Scalability**
   - Each service (e.g., Lambda, API Gateway, Kinesis) can scale independently based on load.
   - Stateless Lambda functions allow for horizontal scaling.

3. **Resilience and Reliability**
   - **API Gateway** handles validation and authentication before passing requests to the backend.
   - **Event-driven architecture** with SNS and Kinesis enhances fault tolerance.
   - **CloudWatch** provides monitoring and alerting.

4. **Security**
   - **Cognito Authentication** ensures only authorized users can access the API.
   - **API Gateway validation** prevents invalid payloads from reaching the backend.
   - **IAM Policies** are used to restrict service permissions (e.g., SNS and Kinesis access).

## Prerequisites
- Node.js (v16 or above)
- AWS CLI configured
- Python 3.9+
- Docker (for Lambda deployment testing)

## Setup Instructions
1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Bootstrap the AWS CDK**
   ```bash
   npx cdk bootstrap
   ```

3. **Deploy the stack**
   ```bash
   npx cdk deploy
   ```

4. **Run Tests Locally**
   ```bash
   pip install -r requirements.txt
   pytest tests/
   ```

## CI Pipeline
The GitHub Actions workflow automatically runs tests on every push or pull request to the `main` branch.

## Project Structure
```
.
├── lambda/
│   └── handler.py        # Python Lambda handler
├── tests/
│   └── test_handler.py   # Unit tests for Lambda
├── lib/
│   └── api-stack.ts      # AWS CDK API stack
├── .github/
│   └── workflows/
│       └── python-lambda-ci.yml  # GitHub Actions CI pipeline
└── README.md
```