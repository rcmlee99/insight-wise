# AWS Serverless API with CDK

A serverless API built with AWS CDK, Lambda, and MongoDB for managing items with automatic geolocation and validation. The API includes comprehensive monitoring, logging, and authentication features.

## Architecture

### Core Components
- **AWS CDK**: Infrastructure as code for AWS resource management
- **Lambda Functions**: Serverless compute for API endpoints
- **MongoDB**: Database for item storage
- **Amazon Cognito**: User authentication and authorization
- **AWS CloudWatch**: Metrics and logging
- **Kinesis**: Real-time log streaming and processing
- **API Gateway**: RESTful API management

### Features
- Automatic geolocation based on postal codes
- Distance and direction calculation from New York
- JWT-based authentication
- Real-time logging and monitoring
- Comprehensive input validation
- Centralized error handling

## API Endpoints

### Items API
All endpoints require Bearer token authentication.

#### Create Item
```
POST /items
Content-Type: application/json
Authorization: Bearer <token>

{
    "name": "Example Item",
    "postcode": "10001",
    "startDate": "2025-03-26T00:00:00Z",
    "users": ["John Doe"]
}
```

#### Get All Items
```
GET /items
Authorization: Bearer <token>
```

#### Get Single Item
```
GET /items/{id}
Authorization: Bearer <token>
```

#### Update Item
```
PATCH /items/{id}
Content-Type: application/json
Authorization: Bearer <token>

{
    "name": "Updated Name",
    "postcode": "10002"
}
```

#### Delete Item
```
DELETE /items/{id}
Authorization: Bearer <token>
```

## Monitoring and Logging

### CloudWatch Metrics
- API Latency
- Status Code Distribution
- Error Rates
- Memory Utilization

### Kinesis Log Streaming
- Real-time log aggregation
- Structured JSON logging
- Lambda PowerTools integration
- Mock consumer for log processing

### CloudWatch Dashboard
Provides visibility into:
- API performance metrics
- Error rates and patterns
- Resource utilization
- Authentication status

## Development Setup

### Prerequisites
- Python 3.11
- AWS CDK CLI
- AWS CLI configured with appropriate credentials
- MongoDB instance or connection string

### Environment Variables
```
USER_POOL_ID=<Cognito User Pool ID>
CLIENT_ID=<Cognito Client ID>
MONGODB_URI=<MongoDB Connection String>
```

### Installation
1. Install dependencies:
```bash
pip install -r lambda_functions/shared/requirements.txt
pip install -r lambda_functions/requirements-dev.txt
```

2. Deploy the stack:
```bash
cdk deploy
```

### Testing
Run the test suite:
```bash
cd lambda_functions
PYTHONPATH=$PYTHONPATH:. pytest tests/ -v
```

## Security
- JWT token validation
- Cognito user pool integration
- API Gateway authorization
- Input validation and sanitization
- Secure MongoDB connection

## Error Handling
- Standardized error responses
- Detailed error logging
- Error tracking via CloudWatch
- Validation error details

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.
