import os
import json
import boto3
import logging
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def process_records(records: List[Dict[str, Any]]) -> None:
    """Process records from Kinesis stream"""
    for record in records:
        try:
            # Decode and parse the record data
            data = json.loads(record['Data'].decode('utf-8'))
            
            # Log the received data for verification
            logger.info(f"Received log entry: {json.dumps(data, indent=2)}")
            
            # Here you would typically:
            # 1. Transform the data if needed
            # 2. Store it in your preferred format/location
            # 3. Trigger any necessary alerts
            
            # For mock purposes, we just acknowledge receipt
            logger.info(f"Successfully processed record {record['SequenceNumber']}")
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            continue

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for processing Kinesis stream records"""
    try:
        process_records(event['Records'])
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Successfully processed records'})
        }
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
