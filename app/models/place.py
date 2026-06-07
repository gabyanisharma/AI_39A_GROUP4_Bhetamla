from app.database import execute_query


class Restaurant:

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

