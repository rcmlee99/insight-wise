import json
import pytest
from unittest.mock import patch, MagicMock
from mock_consumer import process_records, handler

@pytest.fixture
def sample_record():
    return {
        'Data': json.dumps({
            'event': {'test': 'data'},
            'function_name': 'test-function',
            'cold_start': False
        }).encode('utf-8'),
        'SequenceNumber': '123456'
    }

@pytest.fixture
def sample_kinesis_event(sample_record):
    return {
        'Records': [sample_record]
    }

def test_process_records(sample_record):
    # Test successful processing
    records = [sample_record]
    process_records(records)  # Should not raise any exception

    # Test with invalid JSON data
    invalid_record = {
        'Data': b'invalid json',
        'SequenceNumber': '123456'
    }
    process_records([invalid_record])  # Should handle error gracefully

    # Test with missing required fields
    incomplete_record = {
        'Data': json.dumps({'partial': 'data'}).encode('utf-8'),
        'SequenceNumber': '123456'
    }
    process_records([incomplete_record])  # Should handle error gracefully

def test_handler(sample_kinesis_event):
    # Test successful processing
    response = handler(sample_kinesis_event, None)
    assert response['statusCode'] == 200
    assert 'Successfully processed records' in response['body']

    # Test with invalid event structure
    invalid_event = {}
    response = handler(invalid_event, None)
    assert response['statusCode'] == 500
    assert 'error' in response['body']

    # Test with processing error
    with patch('mock_consumer.process_records', side_effect=Exception('Processing error')):
        response = handler(sample_kinesis_event, None)
        assert response['statusCode'] == 500
        assert 'Processing error' in response['body']
