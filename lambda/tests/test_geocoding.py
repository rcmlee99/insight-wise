import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch
from shared.geocoding import get_coordinates, calculate_distance_from_ny, get_direction_from_ny

@patch('shared.geocoding.requests.get')
def test_get_coordinates(mock_get):
    # Mock successful API response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        'places': [{
            'latitude': '40.7128',
            'longitude': '-74.0060'
        }]
    }

    coordinates = get_coordinates("10001")
    assert coordinates == (40.7128, -74.0060)
    mock_get.assert_called_once_with('https://api.zippopotam.us/us/10001')

    # Test API error
    mock_get.return_value.status_code = 404
    coordinates = get_coordinates("invalid_postcode")
    assert coordinates is None

    # Test network error
    mock_get.side_effect = Exception("Network error")
    coordinates = get_coordinates("10001")
    assert coordinates is None

def test_calculate_distance_from_ny():
    # Test points at known distances from NY
    distance = calculate_distance_from_ny(40.7128, -74.0060)  # NY to NY
    assert distance == 0.0

    # Test different directions
    distance_north = calculate_distance_from_ny(42.7128, -74.0060)  # North of NY
    assert distance_north > 0

def test_get_direction_from_ny():
    # Test cardinal directions
    assert get_direction_from_ny(42.7128, -75.0060) == "NW"  # Northwest
    assert get_direction_from_ny(42.7128, -73.0060) == "NE"  # Northeast
    assert get_direction_from_ny(38.7128, -75.0060) == "SW"  # Southwest
    assert get_direction_from_ny(38.7128, -73.0060) == "SE"  # Southeast