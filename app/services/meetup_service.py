import math

def calculate_walking_metrics(start_lat, start_lng, dest_lat, dest_lng):
    """
    Calculates the distance between two GPS coordinates using the Haversine formula
    and estimates walking time based on an average speed of 5 km/h.
    
    Returns:
        tuple: (distance_km, walking_time_minutes)
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert decimal degrees to radians
    lat1, lon1 = math.radians(float(start_lat)), math.radians(float(start_lng))
    lat2, lon2 = math.radians(float(dest_lat)), math.radians(float(dest_lng))

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_km = R * c
    
    # walking speed: 5 km/h
    # Time (min) = (distance / 5) * 60
    walking_time_min = (distance_km / 5.0) * 60

    return round(distance_km, 2), round(walking_time_min, 1)