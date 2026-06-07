from app.database import execute_query
<<<<<<< HEAD
import math


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians,
                                  [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2 +
         math.cos(lat1) * math.cos(lat2) *
         math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))
=======
>>>>>>> f5cac7472e9f8369ce88e39c2cfba52bb6dd62b4


class Restaurant:

<<<<<<< HEAD
    @staticmethod
    def get_all(filters=None):
        """Get all active restaurants with optional filters."""
        query  = "SELECT * FROM restaurants WHERE is_active = TRUE"
        params = []

        if filters:
            if filters.get('cuisine'):
                query += " AND cuisine = %s"
                params.append(filters['cuisine'])

            if filters.get('price_range'):
                query += " AND price_range = %s"
                params.append(filters['price_range'])

            if filters.get('ambience'):
                query += " AND ambience = %s"
                params.append(filters['ambience'])

            if filters.get('min_rating'):
                query += " AND rating >= %s"
                params.append(filters['min_rating'])

            if filters.get('category'):
                query += " AND category = %s"
                params.append(filters['category'])

        query += " ORDER BY rating DESC"
        return execute_query(query, params if params else None,
                             fetch=True)

    @staticmethod
    def get_by_id(restaurant_id):
        query = "SELECT * FROM restaurants WHERE id = %s"
        results = execute_query(query, (restaurant_id,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_nearby(lat, lng, radius_km=3.0, filters=None):
        """Get restaurants within radius_km of given coordinates."""
        all_restaurants = Restaurant.get_all(filters)
        nearby = []

        for r in all_restaurants:
            if r['latitude'] and r['longitude']:
                dist = calculate_distance(
                    float(lat), float(lng),
                    float(r['latitude']), float(r['longitude'])
                )
                if dist <= radius_km:
                    r['distance_km'] = round(dist, 2)
                    nearby.append(r)

        # Sort by distance
        nearby.sort(key=lambda x: x['distance_km'])
        return nearby

    @staticmethod
    def get_near_midpoint(mid_lat, mid_lng,
                          radius_km=3.0, filters=None):
        """Get restaurants near a meetup midpoint."""
        return Restaurant.get_nearby(
            mid_lat, mid_lng, radius_km, filters
        )

    @staticmethod
    def search(query_str):
        query = """
            SELECT * FROM restaurants
            WHERE is_active = TRUE
            AND (name LIKE %s OR cuisine LIKE %s
                 OR address LIKE %s OR category LIKE %s)
            ORDER BY rating DESC
            LIMIT 20
        """
        s = f"%{query_str}%"
        return execute_query(query, (s, s, s, s), fetch=True)

    @staticmethod
    def get_cuisines():
        query = """
            SELECT DISTINCT cuisine FROM restaurants
            WHERE is_active = TRUE
            ORDER BY cuisine
        """
        results = execute_query(query, fetch=True)
        return [r['cuisine'] for r in results] if results else []

    @staticmethod
    def update_rating(restaurant_id):
        """Recalculate average rating from reviews."""
        query = """
            UPDATE restaurants r
            SET rating = (
                SELECT COALESCE(AVG(rating), 0)
                FROM restaurant_reviews
                WHERE restaurant_id = %s
            ),
            review_count = (
                SELECT COUNT(*)
                FROM restaurant_reviews
                WHERE restaurant_id = %s
            )
            WHERE r.id = %s
        """
        return execute_query(query,
                             (restaurant_id, restaurant_id,
                              restaurant_id))


class RestaurantReview:

    @staticmethod
    def add(restaurant_id, user_id, rating, review=''):
        query = """
            INSERT INTO restaurant_reviews
            (restaurant_id, user_id, rating, review)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            rating=%s, review=%s
        """
        result = execute_query(
            query,
            (restaurant_id, user_id, rating, review,
             rating, review)
        )
        Restaurant.update_rating(restaurant_id)
        return result

    @staticmethod
    def get_by_restaurant(restaurant_id):
        query = """
            SELECT rr.*, u.full_name, u.profile_pic
            FROM restaurant_reviews rr
            JOIN users u ON rr.user_id = u.id
            WHERE rr.restaurant_id = %s
            ORDER BY rr.created_at DESC
        """
        return execute_query(query, (restaurant_id,), fetch=True)

    @staticmethod
    def get_by_user(user_id, restaurant_id):
        query = """
            SELECT * FROM restaurant_reviews
            WHERE user_id=%s AND restaurant_id=%s
        """
        results = execute_query(query, (user_id, restaurant_id),
                                fetch=True)
        return results[0] if results else None
=======
	@staticmethod
	def get_budget_range():
		"""Return (min, max) of avg_cost_per_person."""
		query = """
			SELECT MIN(avg_cost_per_person) as min_cost,
				   MAX(avg_cost_per_person) as max_cost
			FROM restaurants
			WHERE is_active = TRUE AND avg_cost_per_person IS NOT NULL
		"""
		results = execute_query(query, fetch=True)
		if results and results[0].get('max_cost') is not None:
			return float(results[0].get('min_cost') or 0), float(results[0].get('max_cost'))
		return 0, 5000

	@staticmethod
	def get_all(filters=None, limit=100):
		"""Return list of restaurants applying optional filters.

		Supported filters: max_budget (float)
		"""
		filters = filters or {}
		params = []
		query = """
			SELECT id, name, description, avg_cost_per_person,
				   rating, is_active, thumbnail_url
			FROM restaurants
			WHERE is_active = TRUE
		"""

		if filters.get('max_budget'):
			query += " AND (avg_cost_per_person IS NULL OR avg_cost_per_person <= %s)"
			params.append(float(filters['max_budget']))

		query += " ORDER BY rating DESC LIMIT %s"
		params.append(limit)

		return execute_query(query, tuple(params), fetch=True)

	@staticmethod
	def search(q, filters=None, limit=50):
		filters = filters or {}
		params = []
		query = """
			SELECT id, name, description, avg_cost_per_person,
				   rating, is_active, thumbnail_url
			FROM restaurants
			WHERE is_active = TRUE
			  AND (name LIKE %s OR description LIKE %s)
		"""
		like = f"%{q}%"
		params.extend((like, like))

		if filters.get('max_budget'):
			query += " AND (avg_cost_per_person IS NULL OR avg_cost_per_person <= %s)"
			params.append(float(filters['max_budget']))

		query += " ORDER BY rating DESC LIMIT %s"
		params.append(limit)

		return execute_query(query, tuple(params), fetch=True)

>>>>>>> f5cac7472e9f8369ce88e39c2cfba52bb6dd62b4
