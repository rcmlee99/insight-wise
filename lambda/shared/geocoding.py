import requests
from typing import Tuple, Optional

def get_coordinates(postcode: str) -> Optional[Tuple[float, float]]:
    """Get coordinates from Zippopotam.us API"""
    try:
        response = requests.get(f'https://api.zippopotam.us/us/{postcode}')
        if response.status_code == 200:
            data = response.json()
            return (
                float(data['places'][0]['latitude']),
                float(data['places'][0]['longitude'])
            )
        return None
    except Exception:
        return None

def calculate_distance_from_ny(lat: float, lon: float) -> float:
    """Calculate distance (in miles) from New York"""
    ny_coordinates = (40.7128, -74.0060)  # New York coordinates
    # Use existing distance calculation
    from geopy.distance import geodesic
    return round(geodesic(ny_coordinates, (lat, lon)).miles, 2)

def get_direction_from_ny(lat: float, lon: float) -> str:
    """Calculate direction (NE, NW, SE, SW) from New York"""
    ny_lat, ny_lon = 40.7128, -74.0060  # New York coordinates

    is_north = lat > ny_lat
    is_east = lon > ny_lon

    if is_north and is_east:
        return "NE"
    elif is_north:
        return "NW"
    elif is_east:
        return "SE"
    else:
        return "SW"