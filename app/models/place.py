import math

from app.database import execute_query


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points."""
    radius_km = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return radius_km * 2 * math.asin(math.sqrt(a))


class Restaurant:

    @staticmethod
    def _select_clause():
        return """
            SELECT id, name, description, address, latitude, longitude,
                   category, cuisine, price_range, avg_cost_per_person,
                   rating, review_count, ambience, image_url, thumbnail_url,
                   opening_time, closing_time, is_active, created_at
            FROM restaurants
        """

    @staticmethod
    def _apply_filters(query, params, filters):
        filters = filters or {}

        if filters.get('cuisine'):
            cuisines = filters['cuisine']
            if not isinstance(cuisines, (list, tuple, set)):
                cuisines = [cuisines]
            
            cuisine_clauses = []
            for cuisine in cuisines:
                cuisine = str(cuisine).strip().lower()
                if not cuisine:
                    continue
                
                # Expand grouped cuisines back into their constituent keywords
                keywords = [cuisine]
                for group_name, kw_list in Restaurant._CUISINE_GROUP_RULES:
                    if cuisine == group_name.lower():
                        keywords.extend(kw_list)
                        break
                
                kw_clauses = []
                for kw in keywords:
                    kw_clauses.append("(LOWER(cuisine) LIKE %s OR LOWER(category) LIKE %s)")
                    like = f"%{kw}%"
                    params.extend([like, like])
                
                if kw_clauses:
                    cuisine_clauses.append("(" + " OR ".join(kw_clauses) + ")")
            
            if cuisine_clauses:
                query += " AND (" + " OR ".join(cuisine_clauses) + ")"

        if filters.get('price_range'):
            query += " AND price_range = %s"
            params.append(filters['price_range'])

        if filters.get('ambience'):
            ambiences = filters['ambience']
            if not isinstance(ambiences, (list, tuple, set)):
                ambiences = [ambiences]
            ambience_clauses = []
            for ambience in ambiences:
                ambience = str(ambience).strip()
                if not ambience:
                    continue
                ambience_clauses.append("LOWER(ambience) LIKE %s")
                params.append(f"%{ambience.lower()}%")
            if ambience_clauses:
                query += " AND (" + " OR ".join(ambience_clauses) + ")"

        if filters.get('min_rating'):
            query += " AND rating >= %s"
            params.append(float(filters['min_rating']))

        if filters.get('category'):
            query += " AND category = %s"
            params.append(filters['category'])

        if filters.get('max_budget'):
            query += " AND (avg_cost_per_person IS NULL OR avg_cost_per_person <= %s)"
            params.append(float(filters['max_budget']))

        return query, params

    @staticmethod
    def get_budget_range():
        query = """
            SELECT MIN(avg_cost_per_person) AS min_cost,
                   MAX(avg_cost_per_person) AS max_cost
            FROM restaurants
            WHERE is_active = TRUE AND avg_cost_per_person IS NOT NULL
        """
        results = execute_query(query, fetch=True)
        if results and results[0].get('max_cost') is not None:
            return (
                float(results[0].get('min_cost') or 0),
                float(results[0].get('max_cost') or 5000),
            )
        return 0, 5000

    @staticmethod
    def get_all(filters=None, limit=None):
        query = Restaurant._select_clause() + " WHERE is_active = TRUE"
        params = []
        query, params = Restaurant._apply_filters(query, params, filters)
        query += " ORDER BY rating DESC, name ASC"
        if limit:
            query += " LIMIT %s"
            params.append(int(limit))
        return execute_query(query, tuple(params) if params else None, fetch=True)

    @staticmethod
    def get_by_id(restaurant_id):
        query = Restaurant._select_clause() + " WHERE id = %s"
        results = execute_query(query, (restaurant_id,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_nearby(lat, lng, radius_km=100.0, filters=None):
        all_restaurants = Restaurant.get_all(filters)
        nearby = []

        for restaurant in all_restaurants:
            if restaurant.get('latitude') and restaurant.get('longitude'):
                distance = calculate_distance(
                    float(lat),
                    float(lng),
                    float(restaurant['latitude']),
                    float(restaurant['longitude']),
                )
                if distance <= radius_km:
                    restaurant['distance_km'] = round(distance, 2)
                    nearby.append(restaurant)

        nearby.sort(key=lambda item: item['distance_km'])
        return nearby

    @staticmethod
    def get_near_midpoint(mid_lat, mid_lng, radius_km=100.0, filters=None):
        return Restaurant.get_nearby(mid_lat, mid_lng, radius_km, filters)

    @staticmethod
    def search(query_str, filters=None, limit=50):
        query = Restaurant._select_clause() + """
            WHERE is_active = TRUE
              AND (name LIKE %s OR cuisine LIKE %s
                   OR address LIKE %s OR category LIKE %s
                   OR description LIKE %s)
        """
        like = f"%{query_str}%"
        params = [like, like, like, like, like]
        query, params = Restaurant._apply_filters(query, params, filters)
        query += " ORDER BY rating DESC, name ASC LIMIT %s"
        params.append(int(limit))
        return execute_query(query, tuple(params), fetch=True)

    @staticmethod
    def get_cuisines():
        query = """
            SELECT DISTINCT cuisine FROM restaurants
            WHERE is_active = TRUE AND cuisine IS NOT NULL
            ORDER BY cuisine
        """
        results = execute_query(query, fetch=True)
        raw = [row['cuisine'] for row in results] if results else []
        return Restaurant._normalize_cuisine_groups(raw)

    # Maps the messy, free-text "cuisine" values in the restaurants table
    # down to a short list of broad categories suitable for a quick-pick UI.
    _CUISINE_GROUP_RULES = [
        ('Nepali',             ['nepali', 'newari', 'thakali']),
        ('Indian',             ['indian']),
        ('Asian',              ['asian', 'chinese', 'japanese', 'thai', 'sushi', 'korean']),
        ('Coffee & Cafe',      ['coffee', 'cafe', 'craft coffee']),
        ('Bakery & Desserts',  ['bakery', 'dessert', 'pastry']),
        ('Continental',        ['continental', 'french', 'italian', 'mediterranean']),
        ('Fast Food',          ['fast food', 'burger', 'fried chicken', 'grilled chicken', 'bbq']),
        ('Vegetarian & Vegan', ['vegetarian', 'vegan']),
        ('Bar & Cocktails',    ['bar', 'cocktail', 'tapas']),
        ('Comfort Food',       ['comfort food', 'breakfast', 'brunch']),
    ]

    @staticmethod
    def _normalize_cuisine_groups(raw_values):
        seen = []
        for value in raw_values:
            lower = (value or '').lower()
            matched = None
            for group_name, keywords in Restaurant._CUISINE_GROUP_RULES:
                if any(kw in lower for kw in keywords):
                    matched = group_name
                    break
            if not matched:
                # Anything that doesn't match a known group keeps its
                # original label rather than being silently dropped.
                matched = value
            if matched not in seen:
                seen.append(matched)
        return sorted(seen)

    @staticmethod
    def update_rating(restaurant_id):
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
        return execute_query(query, (restaurant_id, restaurant_id, restaurant_id))


class RestaurantReview:

    @staticmethod
    def add(restaurant_id, user_id, rating, review=''):
        query = """
            INSERT INTO restaurant_reviews
            (restaurant_id, user_id, rating, review)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            rating = VALUES(rating),
            review = VALUES(review)
        """
        result = execute_query(query, (restaurant_id, user_id, rating, review))
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
            WHERE user_id = %s AND restaurant_id = %s
        """
        results = execute_query(query, (user_id, restaurant_id), fetch=True)
        return results[0] if results else None

class RestaurantOffer:
    @staticmethod
    def get_all_active():
        query = """
            SELECT o.*, r.name as restaurant_name, r.cuisine, r.rating, 
                   r.avg_cost_per_person, r.latitude, r.longitude
            FROM restaurant_offers o
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE o.is_active = TRUE
              AND o.valid_until >= CURDATE()
            ORDER BY o.valid_until ASC
        """
        return execute_query(query, fetch=True)

    @staticmethod
    def get_active_by_restaurant(restaurant_id):
        query = """
            SELECT * FROM restaurant_offers
            WHERE restaurant_id = %s
              AND is_active = TRUE
              AND valid_until >= CURDATE()
            ORDER BY valid_until ASC
        """
        return execute_query(query, (restaurant_id,), fetch=True)

    @staticmethod
    def save_offer(user_id, offer_id):
        query = """
            INSERT IGNORE INTO user_saved_offers (user_id, offer_id, remind_me)
            VALUES (%s, %s, FALSE)
        """
        return execute_query(query, (user_id, offer_id))

    @staticmethod
    def toggle_reminder(user_id, offer_id, remind_me):
        query = """
            UPDATE user_saved_offers
            SET remind_me = %s
            WHERE user_id = %s AND offer_id = %s
        """
        return execute_query(query, (remind_me, user_id, offer_id))

    @staticmethod
    def get_saved_by_user(user_id):
        query = """
            SELECT o.*, uso.remind_me, uso.saved_at, r.name as restaurant_name
            FROM user_saved_offers uso
            JOIN restaurant_offers o ON uso.offer_id = o.id
            JOIN restaurants r ON o.restaurant_id = r.id
            WHERE uso.user_id = %s
              AND o.valid_until >= CURDATE()
            ORDER BY o.valid_until ASC
        """
        return execute_query(query, (user_id,), fetch=True)

    @staticmethod
    def is_saved(user_id, offer_id):
        query = "SELECT 1 FROM user_saved_offers WHERE user_id = %s AND offer_id = %s"
        result = execute_query(query, (user_id, offer_id), fetch=True)
        return bool(result)
