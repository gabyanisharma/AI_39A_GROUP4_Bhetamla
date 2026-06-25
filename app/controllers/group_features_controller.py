import os
import ssl
import json as _json
import urllib.parse
import urllib.request
from uuid import uuid4

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CONTEXT = ssl.create_default_context()

from flask import request, jsonify, render_template, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename

from app.auth import get_current_user_id, is_logged_in
from app.database import execute_query
from app.models.meetup import Meetup, MeetupMember
from app.models.group_vote import GroupVote
from app.models.meetup_gallery import MeetupGallery
from app.models.group_chat import FriendGroup, GroupChat
from app.models.achievement import Achievement
from app.models.place import Restaurant
from app.controllers.notification_controller import send_notification
from app.services import achievement_service


ALLOWED_GALLERY = {'jpg', 'jpeg', 'png'}
MAX_GALLERY_BYTES = 5 * 1024 * 1024


def _accepted_member(meetup_id, user_id):
    rows = execute_query(
        """
        SELECT id FROM meetup_members
        WHERE meetup_id = %s AND user_id = %s AND status = 'accepted'
        """,
        (meetup_id, user_id), fetch=True
    )
    return bool(rows)


def _organiser(meetup_id, user_id):
    meetup = Meetup.get_by_id(meetup_id)
    return meetup and meetup['created_by'] == user_id


def groups_page():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    from app.models.base_model import Friend
    user_id = get_current_user_id()
    meetups = Meetup.get_by_user(user_id, include_hidden=False)

    friends          = Friend.get_friends(user_id) or []
    pending_requests = Friend.get_pending_requests(user_id) or []
    sent_requests    = Friend.get_sent_requests(user_id) or []

    chat_groups = FriendGroup.get_for_user(user_id)
    active_chat_group = chat_groups[0] if chat_groups else None
    achievements = Achievement.get_user_achievements(user_id)
    restaurants = Restaurant.get_all(limit=20) or []

    return render_template(
        'meetup/groups.html',
        meetups=meetups,
        friends=friends,
        pending_requests=pending_requests,
        sent_requests=sent_requests,
        chat_groups=chat_groups,
        active_chat_group=active_chat_group,
        achievements=achievements,
        restaurants=restaurants,
        current_user_id=user_id,
    )


def gallery_page():
    """Render the standalone meetup gallery page."""
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id = get_current_user_id()
    meetups = Meetup.get_by_user(user_id, include_hidden=False)

    return render_template(
        'meetup/gallery.html',
        meetups=meetups,
        current_user_id=user_id,
    )


def hide_from_groups(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    execute_query(
        """
        UPDATE meetup_members SET hidden_from_groups = TRUE
        WHERE meetup_id = %s AND user_id = %s
        """,
        (meetup_id, user_id)
    )
    flash('Meetup removed from My Groups. It remains in your history and analytics.', 'info')
    return redirect(url_for('meetup.groups'))


def start_vote(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    if not _organiser(meetup_id, user_id):
        return jsonify({'success': False, 'message': 'Only the organiser can start a vote.'}), 403

    if GroupVote.get_active_for_meetup(meetup_id):
        return jsonify({'success': False, 'message': 'A vote is already open.'}), 400

    data = request.get_json(silent=True) or {}
    restaurant_ids = data.get('restaurant_ids') or []
    options = []

    # Use provided restaurant IDs first
    if len(restaurant_ids) >= 1:
        for rid in restaurant_ids[:3]:
            r = Restaurant.get_by_id(int(rid))
            if r:
                options.append({
                    'restaurant_id': r['id'],
                    'label': r['name'],
                    'address': r.get('address'),
                })

    # Fill up from member recommended places
    if len(options) < 3:
        from app.models.meetup_preference import MeetupPlanPreference
        prefs = MeetupPlanPreference.get_for_meetup(meetup_id)
        for p in prefs:
            if len(options) >= 3:
                break
            if p.get('selected_venue') and not any(o.get('label') == p['selected_venue'] for o in options):
                options.append({
                    'restaurant_id': None,
                    'label': p['selected_venue'],
                    'address': f"{p.get('selected_venue_lat', '')},{p.get('selected_venue_lng', '')}".strip(',') or None
                })

    # Fill up from DB restaurants if needed
    if len(options) < 3:
        defaults = Restaurant.get_all(limit=10) or []
        for r in defaults:
            if len(options) >= 3:
                break
            if not any(o.get('restaurant_id') == r['id'] for o in options):
                options.append({
                    'restaurant_id': r['id'],
                    'label': r['name'],
                    'address': r.get('address'),
                })

    # If still not enough, pad with generic placeholder options
    fallbacks = ['Option A', 'Option B', 'Option C']
    idx = 0
    while len(options) < 3:
        options.append({'restaurant_id': None, 'label': fallbacks[idx % 3], 'address': None})
        idx += 1

    vote_id = GroupVote.create(meetup_id, user_id, options[:3], hours=24)
    achievement_service.on_vote_created(user_id)

    members = execute_query(
        """
        SELECT user_id FROM meetup_members
        WHERE meetup_id = %s AND status = 'accepted' AND user_id != %s
        """,
        (meetup_id, user_id), fetch=True
    ) or []
    meetup = Meetup.get_by_id(meetup_id)
    for m in members:
        send_notification(
            m['user_id'],
            'Group Vote Started',
            f'Vote for a venue in "{meetup["title"]}" — closes in 24 hours.',
            type='vote',
            link=f'/meetup/groups?meetup={meetup_id}'
        )

    return jsonify({'success': True, 'vote_id': vote_id})


def cast_vote(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    if not _accepted_member(meetup_id, user_id):
        return jsonify({'success': False, 'message': 'Not an accepted member.'}), 403

    GroupVote.close_expired()
    vote = GroupVote.get_active_for_meetup(meetup_id)
    if not vote:
        return jsonify({'success': False, 'message': 'No open vote.'}), 400

    data = request.get_json(silent=True) or {}
    option_id = data.get('option_id')
    if not option_id:
        return jsonify({'success': False, 'message': 'option_id required.'}), 400

    GroupVote.cast_vote(vote['id'], user_id, int(option_id))
    return jsonify({
        'success': True,
        'results': GroupVote.get_results(vote['id']),
        'my_vote': int(option_id),
    })


def vote_results(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    GroupVote.close_expired()
    vote_rows = execute_query(
        """
        SELECT * FROM venue_votes WHERE meetup_id = %s
        ORDER BY created_at DESC LIMIT 1
        """,
        (meetup_id,), fetch=True
    )
    if not vote_rows:
        return jsonify({'success': True, 'vote': None, 'results': []})
    vote = vote_rows[0]
    if vote['status'] == 'open' and vote['deadline']:
        from datetime import datetime
        if vote['deadline'] <= datetime.now():
            finalize_result = GroupVote._finalize_vote(vote['id'], meetup_id)
            vote = GroupVote.get_by_id(vote['id'])
            is_tie = isinstance(finalize_result, dict) and finalize_result.get('is_tie')
            members = execute_query(
                """
                SELECT user_id FROM meetup_members
                WHERE meetup_id = %s AND status = 'accepted'
                """,
                (meetup_id,), fetch=True
            ) or []
            meetup = Meetup.get_by_id(meetup_id)
            if is_tie:
                tied_names = ', '.join(o['label'] for o in finalize_result['tied_options'][:3])
                for m in members:
                    send_notification(
                        m['user_id'],
                        'Vote Tied — Revote Needed',
                        f'Voting for "{meetup["title"]}" ended in a tie ({tied_names}). A new vote has been started.',
                        type='vote',
                        link=f'/meetup/view/{meetup_id}'
                    )
                # Auto-start a new vote with the tied options
                tied_specs = [{'label': o['label'], 'address': o.get('address'), 'restaurant_id': o.get('restaurant_id')}
                              for o in finalize_result['tied_options'][:3]]
                GroupVote.create(meetup_id, vote['created_by'], tied_specs, hours=24)
            else:
                winner_name = meetup.get('winning_venue_name') or 'the top choice'
                for m in members:
                    send_notification(
                        m['user_id'],
                        'Vote Closed',
                        f'Venue voting for "{meetup["title"]}" ended. Winner: {winner_name}.',
                        type='vote',
                        link=f'/meetup/view/{meetup_id}'
                    )

    user_id = get_current_user_id()
    return jsonify({
        'success': True,
        'vote': {
            'id': vote['id'],
            'status': vote['status'],
            'deadline': vote['deadline'].isoformat() if vote.get('deadline') else None,
        } if vote else None,
        'results': GroupVote.get_results(vote['id']) if vote else [],
        'my_vote': GroupVote.get_user_cast(vote['id'], user_id) if vote else None,
    })


def upload_gallery(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    if not _accepted_member(meetup_id, user_id):
        return jsonify({'success': False, 'message': 'Not an accepted member.'}), 403

    if 'photo' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'}), 400

    file = request.files['photo']
    if not file.filename:
        return jsonify({'success': False, 'message': 'Empty filename.'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_GALLERY:
        return jsonify({'success': False, 'message': 'Only JPG/PNG allowed.'}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_GALLERY_BYTES:
        return jsonify({'success': False, 'message': 'File must be under 5MB.'}), 400

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'gallery')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{meetup_id}_{user_id}_{uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    is_public = request.form.get('is_public', '1') == '1'
    caption = request.form.get('caption', '').strip()
    photo_id = MeetupGallery.add(
        meetup_id, user_id,
        f'uploads/gallery/{filename}',
        caption, is_public
    )

    members = execute_query(
        """
        SELECT user_id FROM meetup_members
        WHERE meetup_id = %s AND status = 'accepted' AND user_id != %s
        """,
        (meetup_id, user_id), fetch=True
    ) or []
    meetup = Meetup.get_by_id(meetup_id)
    for m in members:
        send_notification(
            m['user_id'],
            'New Gallery Photo',
            f'A new photo was added to "{meetup["title"]}".',
            type='gallery',
            link=f'/meetup/groups?meetup={meetup_id}'
        )

    return jsonify({
        'success': True,
        'photo_id': photo_id,
        'url': url_for('static', filename=f'uploads/gallery/{filename}'),
    })


def gallery_list(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    if not _accepted_member(meetup_id, user_id) and not _organiser(meetup_id, user_id):
        return jsonify({'success': False, 'message': 'Not a member.'}), 403
    photos = MeetupGallery.get_for_meetup(meetup_id, user_id)
    serialized = []
    for p in photos:
        serialized.append({
            'id': p['id'],
            'user_id': p['user_id'],
            'url': url_for('static', filename=p['file_path']),
            'caption': p.get('caption') or '',
            'is_public': bool(p.get('is_public')),
            'like_count': p.get('like_count', 0),
            'comment_count': p.get('comment_count', 0),
            'full_name': p.get('full_name'),
        })
    return jsonify({'success': True, 'photos': serialized})


def delete_gallery_photo(photo_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    MeetupGallery.delete(photo_id, get_current_user_id())
    return jsonify({'success': True})


def toggle_gallery_like(photo_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    liked = MeetupGallery.toggle_like(photo_id, get_current_user_id())
    return jsonify({'success': True, 'liked': liked})


def gallery_comment(photo_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    data = request.get_json(silent=True) or {}
    comment = (data.get('comment') or '').strip()
    if not comment:
        return jsonify({'success': False, 'message': 'Comment required.'}), 400
    MeetupGallery.add_comment(photo_id, get_current_user_id(), comment)
    comments = MeetupGallery.get_comments(photo_id)
    return jsonify({'success': True, 'comments': comments})


def gallery_privacy(photo_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    data = request.get_json(silent=True) or {}
    is_public = bool(data.get('is_public', True))
    MeetupGallery.set_privacy(photo_id, get_current_user_id(), is_public)
    return jsonify({'success': True, 'is_public': is_public})


def chat_messages(group_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    if not FriendGroup.is_member(group_id, user_id):
        return jsonify({'success': False, 'message': 'Not a group member.'}), 403

    messages = GroupChat.get_messages(group_id)
    GroupChat.mark_all_read(group_id, user_id)
    typing = GroupChat.get_typing_users(group_id, user_id)
    enriched = []
    for msg in messages:
        enriched.append({
            **msg,
            'read_by': GroupChat.get_read_receipts(msg['id']),
            'profile_pic': msg.get('profile_pic'),
            'created_at': msg['created_at'].isoformat() if msg.get('created_at') else None,
        })
    return jsonify({
        'success': True,
        'messages': enriched,
        'typing': [t['full_name'] for t in typing],
    })


def send_chat_message(group_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    if not FriendGroup.is_member(group_id, user_id):
        return jsonify({'success': False, 'message': 'Not a group member.'}), 403

    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'success': False, 'message': 'Message is empty.'}), 400

    msg_id = GroupChat.post_message(group_id, user_id, body)
    msg = GroupChat.get_message(msg_id)
    achievement_service.on_chat_message(user_id)

    # Broadcast to room so active websocket clients receive the message
    try:
        from app import socketio
        payload = {
            'id': msg_id,
            'group_id': group_id,
            'user_id': user_id,
            'full_name': msg['full_name'],
            'profile_pic': msg.get('profile_pic'),
            'body': body,
            'created_at': msg['created_at'].isoformat() if msg.get('created_at') else None
        }
        socketio.emit('new_message', payload, to=f'group_{group_id}')
    except Exception as e:
        print(f"Error broadcasting from HTTP fallback: {e}")

    return jsonify({
        'success': True,
        'message': {
            'id': msg_id,
            'group_id': group_id,
            'user_id': user_id,
            'full_name': msg['full_name'],
            'profile_pic': msg.get('profile_pic'),
            'body': body,
            'created_at': msg['created_at'].isoformat() if msg.get('created_at') else None,
            'read_by': [],
        }
    })


def record_budget_split(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    execute_query(
        """
        INSERT INTO budget_split_log (user_id, meetup_id) VALUES (%s, %s)
        """,
        (user_id, meetup_id)
    )
    achievement_service.on_budget_split_used(user_id)
    return jsonify({'success': True})


# ── Chat message translation (US17) ──────────────
TRANSLATE_LANGS = {
    'en': 'English',
    'ne': 'Nepali',
    'np': 'Nepali',   
}


def _translate_text(text, target):
    """Translate via Google's free gtx endpoint (no API key). Source is
    auto-detected. Returns the translated string, or None on failure."""
    url = ('https://translate.googleapis.com/translate_a/single'
           '?client=gtx&sl=auto&tl=' + urllib.parse.quote(target) +
           '&dt=t&q=' + urllib.parse.quote(text))
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=6, context=_SSL_CONTEXT) as resp:
        data = _json.loads(resp.read().decode('utf-8'))
    segments = data[0] or []
    translated = ''.join(seg[0] for seg in segments if seg and seg[0])
    return translated or None


def translate_message():
    """Translate a chat message into the user's preferred language."""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    payload = request.get_json(silent=True) or {}
    text = (payload.get('text') or '').strip()
    target = payload.get('target') or session.get('language') or 'en'
    if target == 'np':
        target = 'ne'   
    if target not in TRANSLATE_LANGS:
        target = 'en'

    if not text:
        return jsonify({'success': False, 'message': 'Nothing to translate.'}), 400

    try:
        translated = _translate_text(text, target)
    except Exception as exc:
        print('Translation error:', exc)
        return jsonify({'success': False,
                        'message': 'Translation service unavailable.'}), 502

    if not translated:
        return jsonify({'success': False, 'message': 'Could not translate.'}), 502

    return jsonify({
        'success': True,
        'translated': translated,
        'target': target,
        'target_name': TRANSLATE_LANGS[target],
    })
