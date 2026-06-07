from flask import render_template, request, jsonify, redirect, url_for
from app.models.place import Restaurant
from app.auth import is_logged_in


def _build_filters(args):
	filters = {}
	if args.get('max_budget'):
		try:
			filters['max_budget'] = float(args.get('max_budget'))
		except (ValueError, TypeError):
			pass
	return filters


def restaurants():
	if not is_logged_in():
		return redirect(url_for('auth.login'))

	# Budget range for slider
	budget_min, budget_max = Restaurant.get_budget_range()

	# Optional meetup context for group budget
	meetup_id = request.args.get('meetup_id')
	group_budget = None
	if meetup_id:
		try:
			from app.models.meetup import Meetup
			meetup = Meetup.get_by_id(meetup_id)
			group_budget = meetup.get('group_budget') if meetup else None
		except ImportError:
			group_budget = None

	return render_template('place/restaurants.html',
						   budget_min=budget_min,
						   budget_max=budget_max,
						   group_budget=group_budget)


def api_filter_restaurants():
	# AJAX endpoint to return JSON list of restaurants
	args = request.args
	filters = _build_filters(args)
	rows = Restaurant.get_all(filters=filters, limit=200)

	def serialize(r):
		return {
			'id': int(r.get('id')),
			'name': r.get('name'),
			'description': r.get('description'),
			'avg_cost_per_person': float(r.get('avg_cost_per_person') or 0),
			'rating': float(r.get('rating') or 0),
			'thumbnail_url': r.get('thumbnail_url')
		}

	return jsonify([serialize(r) for r in (rows or [])])

