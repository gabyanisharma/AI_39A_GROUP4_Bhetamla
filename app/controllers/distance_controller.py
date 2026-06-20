from flask import Blueprint, request, jsonify
import requests

distance_bp = Blueprint('distance_bp', __name__)

@distance_bp.route('/api/calculate-distance', methods=['POST'])
def calculate_distance():
    data = request.json
    try:
        origin = f"{data['user_lng']},{data['user_lat']}"
        dest = f"{data['dest_lng']},{data['dest_lat']}"
        url = f"http://router.project-osrm.org/route/v1/walking/{origin};{dest}?overview=false"
        response = requests.get(url).json()
        
        if response.get('code') == 'Ok':
            route = response['routes'][0]
            return jsonify({
                'distance_km': round(route['distance'] / 1000, 2),
                'duration_min': round(route['duration'] / 60)
            })
        return jsonify({'error': 'Calculation failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
