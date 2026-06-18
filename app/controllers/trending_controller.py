from flask import (render_template, request, redirect,
                   url_for, flash, jsonify)
from app.auth import get_current_user_id, is_logged_in
from app.models.trending_spot import (
    TrendingSpot, SpotInteraction, SpotRecommendation
)

VALID_INTERACTIONS = {'view', 'like', 'save', 'share', 'visit'}


def _build_filters(args):
    """Build a filter dict from request args for the Explore feed."""
    filters = {}
    if args.get('cuisine'):
        filters['cuisine'] = args.get('cuisine')
    if args.get('category'):
        filters['category'] = args.get('category')
    if args.get('price_range'):
        filters['price_range'] = args.get('price_range')
    if args.get('ambience'):
        filters['ambience'] = args.get('ambience')
    if args.get('min_rating'):
        try:
            filters['min_rating'] = float(args.get('min_rating'))
        except (ValueError, TypeError):
            pass
    return filters


# ── Explore feed page ──────────────────────────────────────────────
def explore_feed():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id = get_current_user_id()
    filters = _build_filters(request.args)
    search_q = request.args.get('q')

    if search_q:
        spots = TrendingSpot.search(search_q)
        featured = []
    else:
        spots = TrendingSpot.get_feed(filters)
        featured = TrendingSpot.get_featured(limit=3)

    recommendations = SpotRecommendation.generate_for_user(user_id, limit=6)

    liked = SpotInteraction.liked_spot_ids(user_id)
    saved = SpotInteraction.saved_spot_ids(user_id)

    return render_template('place/explore.html',
                           spots=spots or [],
                           featured=featured or [],
                           recommendations=recommendations or [],
                           cuisines=TrendingSpot.get_cuisines(),
                           filters=filters,
                           search_q=search_q or '',
                           liked_ids=liked,
                           saved_ids=saved)


# ── Spot detail page ───────────────────────────────────────────────
def spot_detail(spot_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    spot = TrendingSpot.get_by_id(spot_id)
    if not spot:
        flash('Spot not found.', 'error')
        return redirect(url_for('explore.feed'))

    user_id = get_current_user_id()
    # Viewing a spot is itself a (light) signal that feeds trending.
    SpotInteraction.record(user_id, spot_id, 'view')

    return render_template('place/spot_detail.html',
                           spot=spot,
                           is_liked=SpotInteraction.has_interacted(user_id, spot_id, 'like'),
                           is_saved=SpotInteraction.has_interacted(user_id, spot_id, 'save'))


# ── Record an interaction (AJAX) ───────────────────────────────────
def toggle_interaction(spot_id):
    """Toggle a like/save/share/visit on a spot and return JSON state."""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data = request.get_json(silent=True) or {}
    interaction_type = data.get('type') or request.form.get('type', 'like')

    if interaction_type not in VALID_INTERACTIONS:
        return jsonify({'success': False, 'message': 'Invalid interaction.'}), 400

    if not TrendingSpot.get_by_id(spot_id):
        return jsonify({'success': False, 'message': 'Spot not found.'}), 404

    user_id = get_current_user_id()
    already = SpotInteraction.has_interacted(user_id, spot_id, interaction_type)

    # Likes and saves toggle; shares/visits/views just accumulate.
    if already and interaction_type in ('like', 'save'):
        SpotInteraction.remove(user_id, spot_id, interaction_type)
        active = False
    else:
        SpotInteraction.record(user_id, spot_id, interaction_type)
        active = True

    spot = TrendingSpot.get_by_id(spot_id)
    return jsonify({
        'success': True,
        'type': interaction_type,
        'active': active,
        'trend_score': float(spot['trend_score'] or 0)
    })


# ── Saved spots page ───────────────────────────────────────────────
def saved_spots():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id = get_current_user_id()
    spots = SpotInteraction.get_user_interactions(user_id, 'save')
    return render_template('place/explore.html',
                           spots=spots or [],
                           featured=[],
                           recommendations=[],
                           cuisines=TrendingSpot.get_cuisines(),
                           filters={},
                           search_q='',
                           saved_view=True,
                           liked_ids=SpotInteraction.liked_spot_ids(user_id),
                           saved_ids=SpotInteraction.saved_spot_ids(user_id))


# ── Dismiss a recommendation ───────────────────────────────────────
def dismiss_recommendation(spot_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401

    user_id = get_current_user_id()
    SpotRecommendation.dismiss(user_id, spot_id)
    return jsonify({'success': True})
