from app.database import execute_query


class TrendingSpot:
    """Curated meetup spots surfaced in the Explore feed."""

    @staticmethod
    def _select_clause():
        return """
            SELECT id, name, description, address, latitude, longitude,
                   category, cuisine, ambience, price_range, avg_cost_per_person,
                   rating, review_count, trend_score, image_url, thumbnail_url,
                   is_active, is_featured, created_at, updated_at
            FROM trending_spots
        """

    @staticmethod
    def _apply_filters(query, params, filters):
        filters = filters or {}

        if filters.get('cuisine'):
            query += " AND cuisine = %s"
            params.append(filters['cuisine'])

        if filters.get('category'):
            query += " AND category = %s"
            params.append(filters['category'])

        if filters.get('price_range'):
            query += " AND price_range = %s"
            params.append(filters['price_range'])

        if filters.get('ambience'):
            query += " AND ambience = %s"
            params.append(filters['ambience'])

        if filters.get('min_rating'):
            query += " AND rating >= %s"
            params.append(float(filters['min_rating']))

        return query, params

    @staticmethod
    def get_feed(filters=None, limit=24):
        """Return active spots ordered by trend score for the Explore feed."""
        query = TrendingSpot._select_clause() + " WHERE is_active = TRUE"
        params = []
        query, params = TrendingSpot._apply_filters(query, params, filters)
        query += " ORDER BY trend_score DESC, rating DESC, name ASC"
        if limit:
            query += " LIMIT %s"
            params.append(int(limit))
        return execute_query(query, tuple(params) if params else None, fetch=True)

    @staticmethod
    def get_featured(limit=5):
        query = TrendingSpot._select_clause() + """
            WHERE is_active = TRUE AND is_featured = TRUE
            ORDER BY trend_score DESC, rating DESC
            LIMIT %s
        """
        return execute_query(query, (int(limit),), fetch=True)

    @staticmethod
    def get_by_id(spot_id):
        query = TrendingSpot._select_clause() + " WHERE id = %s"
        results = execute_query(query, (spot_id,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def search(query_str, limit=50):
        query = TrendingSpot._select_clause() + """
            WHERE is_active = TRUE
              AND (name LIKE %s OR cuisine LIKE %s
                   OR address LIKE %s OR category LIKE %s
                   OR description LIKE %s)
            ORDER BY trend_score DESC, rating DESC
            LIMIT %s
        """
        like = f"%{query_str}%"
        return execute_query(query, (like, like, like, like, like, int(limit)), fetch=True)

    @staticmethod
    def get_cuisines():
        query = """
            SELECT DISTINCT cuisine FROM trending_spots
            WHERE is_active = TRUE AND cuisine IS NOT NULL
            ORDER BY cuisine
        """
        results = execute_query(query, fetch=True)
        return [row['cuisine'] for row in results] if results else []

    @staticmethod
    def recalculate_trend_score(spot_id):
        """
        Recompute a spot's trend score from recent engagement.

        The score blends weighted interaction counts with the spot's
        rating so that well-loved, actively-engaged spots rise to the top
        of the Explore feed.
        """
        query = """
            UPDATE trending_spots ts
            SET trend_score = (
                SELECT COALESCE(
                    SUM(CASE interaction_type
                            WHEN 'view'  THEN 1
                            WHEN 'like'  THEN 3
                            WHEN 'save'  THEN 4
                            WHEN 'share' THEN 5
                            WHEN 'visit' THEN 6
                            ELSE 1 END), 0)
                FROM user_spot_interactions
                WHERE spot_id = %s
                  AND created_at >= (NOW() - INTERVAL 30 DAY)
            ) + (ts.rating * 2)
            WHERE ts.id = %s
        """
        return execute_query(query, (spot_id, spot_id))


class SpotInteraction:
    """Records of how users engage with trending spots."""

    @staticmethod
    def record(user_id, spot_id, interaction_type):
        """Store an interaction (idempotent per user/spot/type)."""
        query = """
            INSERT INTO user_spot_interactions (user_id, spot_id, interaction_type)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
        """
        result = execute_query(query, (user_id, spot_id, interaction_type))
        TrendingSpot.recalculate_trend_score(spot_id)
        return result

    @staticmethod
    def remove(user_id, spot_id, interaction_type):
        query = """
            DELETE FROM user_spot_interactions
            WHERE user_id = %s AND spot_id = %s AND interaction_type = %s
        """
        result = execute_query(query, (user_id, spot_id, interaction_type))
        TrendingSpot.recalculate_trend_score(spot_id)
        return result

    @staticmethod
    def has_interacted(user_id, spot_id, interaction_type):
        query = """
            SELECT 1 FROM user_spot_interactions
            WHERE user_id = %s AND spot_id = %s AND interaction_type = %s
        """
        return bool(execute_query(query, (user_id, spot_id, interaction_type), fetch=True))

    @staticmethod
    def get_user_interactions(user_id, interaction_type=None):
        """Return spots a user has interacted with, optionally by type."""
        query = """
            SELECT ts.*
            FROM trending_spots ts
            JOIN user_spot_interactions i ON i.spot_id = ts.id
            WHERE i.user_id = %s AND ts.is_active = TRUE
        """
        params = [user_id]
        if interaction_type:
            query += " AND i.interaction_type = %s"
            params.append(interaction_type)
        query += " ORDER BY i.created_at DESC"
        return execute_query(query, tuple(params), fetch=True)

    @staticmethod
    def liked_spot_ids(user_id):
        query = """
            SELECT spot_id FROM user_spot_interactions
            WHERE user_id = %s AND interaction_type = 'like'
        """
        rows = execute_query(query, (user_id,), fetch=True)
        return {row['spot_id'] for row in rows} if rows else set()

    @staticmethod
    def saved_spot_ids(user_id):
        query = """
            SELECT spot_id FROM user_spot_interactions
            WHERE user_id = %s AND interaction_type = 'save'
        """
        rows = execute_query(query, (user_id,), fetch=True)
        return {row['spot_id'] for row in rows} if rows else set()


class SpotRecommendation:
    """Personalised spot recommendations for a user."""

    @staticmethod
    def generate_for_user(user_id, limit=6):
        """
        Build content-based recommendations for a user.

        We look at the cuisines/categories the user has liked or saved and
        surface highly-trending spots in those buckets that they have not
        already engaged with. If there is no history yet, we fall back to
        the top trending spots overall.
        """
        preferences = execute_query(
            """
            SELECT ts.cuisine, ts.category, COUNT(*) AS weight
            FROM user_spot_interactions i
            JOIN trending_spots ts ON ts.id = i.spot_id
            WHERE i.user_id = %s
              AND i.interaction_type IN ('like', 'save', 'visit')
            GROUP BY ts.cuisine, ts.category
            ORDER BY weight DESC
            """,
            (user_id,), fetch=True
        ) or []

        seen_ids = execute_query(
            "SELECT DISTINCT spot_id FROM user_spot_interactions WHERE user_id = %s",
            (user_id,), fetch=True
        ) or []
        seen = {row['spot_id'] for row in seen_ids}

        # Exclude recommendations the user has explicitly dismissed.
        dismissed_ids = execute_query(
            "SELECT spot_id FROM spot_recommendations "
            "WHERE user_id = %s AND is_dismissed = TRUE",
            (user_id,), fetch=True
        ) or []
        seen |= {row['spot_id'] for row in dismissed_ids}

        recommendations = []
        if preferences:
            cuisines = [p['cuisine'] for p in preferences if p['cuisine']]
            categories = [p['category'] for p in preferences if p['category']]
            if cuisines or categories:
                clauses = []
                params = []
                if cuisines:
                    clauses.append("cuisine IN (%s)" % ",".join(["%s"] * len(cuisines)))
                    params.extend(cuisines)
                if categories:
                    clauses.append("category IN (%s)" % ",".join(["%s"] * len(categories)))
                    params.extend(categories)
                query = (
                    TrendingSpot._select_clause()
                    + " WHERE is_active = TRUE AND (" + " OR ".join(clauses) + ")"
                    + " ORDER BY trend_score DESC, rating DESC LIMIT %s"
                )
                params.append(int(limit) + len(seen))
                candidates = execute_query(query, tuple(params), fetch=True) or []
                for spot in candidates:
                    if spot['id'] not in seen:
                        spot['recommendation_reason'] = (
                            f"Because you like {spot['cuisine'] or spot['category']}"
                        )
                        recommendations.append(spot)
                    if len(recommendations) >= limit:
                        break

        if len(recommendations) < limit:
            # Fall back to trending spots the user has not seen yet.
            for spot in TrendingSpot.get_feed(limit=limit + len(seen)) or []:
                if spot['id'] not in seen and all(
                    spot['id'] != r['id'] for r in recommendations
                ):
                    spot.setdefault('recommendation_reason', 'Trending in Kathmandu right now')
                    recommendations.append(spot)
                if len(recommendations) >= limit:
                    break

        return recommendations[:limit]

    @staticmethod
    def add(user_id, spot_id, recommended_by=None, reason=None, score=0):
        """Persist a recommendation (e.g. a friend suggesting a spot)."""
        query = """
            INSERT INTO spot_recommendations
                (user_id, spot_id, recommended_by, recommendation_reason, score)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                recommended_by = VALUES(recommended_by),
                recommendation_reason = VALUES(recommendation_reason),
                score = VALUES(score),
                is_dismissed = FALSE
        """
        return execute_query(query, (user_id, spot_id, recommended_by, reason, score))

    @staticmethod
    def dismiss(user_id, spot_id):
        """Mark a spot as dismissed so it stops appearing in recommendations.

        Recommendations are generated on the fly, so a dismissal may not have
        an existing row yet — upsert one flagged as dismissed.
        """
        query = """
            INSERT INTO spot_recommendations (user_id, spot_id, is_dismissed)
            VALUES (%s, %s, TRUE)
            ON DUPLICATE KEY UPDATE is_dismissed = TRUE
        """
        return execute_query(query, (user_id, spot_id))

    @staticmethod
    def get_saved(user_id):
        query = """
            SELECT ts.*, sr.recommendation_reason, sr.score
            FROM trending_spots ts
            JOIN spot_recommendations sr ON sr.spot_id = ts.id
            WHERE sr.user_id = %s
              AND sr.is_dismissed = FALSE
              AND ts.is_active = TRUE
            ORDER BY sr.score DESC, sr.created_at DESC
        """
        return execute_query(query, (user_id,), fetch=True)
