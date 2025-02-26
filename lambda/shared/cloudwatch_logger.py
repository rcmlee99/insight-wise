import os
import json
import logging
from aws_lambda_powertools import Logger
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.metrics import Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3

# Initialize logger with service name
logger = Logger(service="items-api")
metrics = Metrics(namespace="ItemsAPI")

# Initialize Kinesis client
kinesis_client = boto3.client('kinesis')
STREAM_NAME = os.environ.get('KINESIS_STREAM_NAME')

def setup_logging(handler_name: str):
    """Configure logging for Lambda function"""
    logger.append_keys(handler=handler_name)

    # Set log level from environment variable or default to INFO
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logger.setLevel(log_level)

def log_event(event: dict, context: LambdaContext = None):
    """Log Lambda event details and stream to Kinesis"""
    # Handle None context for test environments
    request_id = getattr(context, 'aws_request_id', 'TEST')
    function_name = getattr(context, 'function_name', 'test-function')
    function_version = getattr(context, 'function_version', 'test')
    memory_limit = getattr(context, 'memory_limit_in_mb', 128)

    log_data = {
        "cold_start": request_id == "LATEST",
        "event": event,
        "function_name": function_name,
        "function_version": function_version,
        "memory_limit": memory_limit
    }

    logger.info("Lambda event", extra=log_data)

    # Only stream to Kinesis if we're not in a test environment
    if STREAM_NAME and context is not None:
        try:
            # Stream log data to Kinesis
            kinesis_client.put_record(
                StreamName=STREAM_NAME,
                Data=json.dumps(log_data),
                PartitionKey=request_id
            )
        except Exception as e:
            logger.warning(f"Failed to stream log to Kinesis: {str(e)}")

def log_api_metrics(operation: str, status_code: int, duration_ms: float):
    """Record API metrics"""
    metrics.add_metric(name="APILatency", unit=MetricUnit.Milliseconds, value=duration_ms)
    metrics.add_metric(name="APIStatus", unit=MetricUnit.Count, value=1)
    metrics.add_dimension(name="Operation", value=operation)
    metrics.add_dimension(name="StatusCode", value=str(status_code))