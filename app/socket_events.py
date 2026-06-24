"""Flask-SocketIO event handlers for group chat."""

from flask import session
from flask_socketio import emit, join_room, leave_room

from app.models.group_chat import FriendGroup, GroupChat
from app.services import achievement_service


def register_socket_events(socketio):

    @socketio.on('join_group')
    def on_join(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        group_id = data.get('group_id')
        if not group_id or not FriendGroup.is_member(int(group_id), user_id):
            return
        join_room(f'group_{group_id}')
        emit('joined', {'group_id': group_id})

    @socketio.on('leave_group')
    def on_leave(data):
        group_id = data.get('group_id')
        if group_id:
            leave_room(f'group_{group_id}')

    @socketio.on('send_message')
    def on_send(data):
        user_id = session.get('user_id')
        if not user_id:
            emit('error', {'message': 'Not logged in'})
            return
        group_id = int(data.get('group_id', 0))
        body = (data.get('body') or '').strip()
        if not body or not group_id:
            return
        if not FriendGroup.is_member(group_id, user_id):
            emit('error', {'message': 'Not a member'})
            return

        msg_id = GroupChat.post_message(group_id, user_id, body)
        msg = GroupChat.get_message(msg_id)
        achievement_service.on_chat_message(user_id)

        from app.controllers.notification_controller import send_notification
        members = FriendGroup.get_members(group_id)
        for m in members:
            if m['id'] != user_id:
                send_notification(
                    m['id'],
                    'New Group Message',
                    f'{msg["full_name"]}: {body[:80]}',
                    type='chat',
                    link='/meetup/groups'
                )

        payload = {
            'id': msg_id,
            'group_id': group_id,
            'user_id': user_id,
            'full_name': msg['full_name'],
            'profile_pic': msg.get('profile_pic'),
            'body': body,
            'created_at': msg['created_at'].isoformat() if msg.get('created_at') else None,
            'read_by': [],
        }
        emit('new_message', payload, room=f'group_{group_id}')

    @socketio.on('typing')
    def on_typing(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        group_id = int(data.get('group_id', 0))
        if not group_id or not FriendGroup.is_member(group_id, user_id):
            return
        GroupChat.set_typing(group_id, user_id)
        from app.database import execute_query
        user = execute_query(
            "SELECT full_name FROM users WHERE id = %s",
            (user_id,), fetch=True
        )
        name = user[0]['full_name'] if user else 'Someone'
        emit('user_typing', {'full_name': name, 'group_id': group_id},
             room=f'group_{group_id}', include_self=False)

    @socketio.on('mark_read')
    def on_mark_read(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        message_id = data.get('message_id')
        group_id = data.get('group_id')
        if message_id:
            GroupChat.mark_read(int(message_id), user_id)
            emit('message_read', {
                'message_id': message_id,
                'user_id': user_id,
            }, room=f'group_{group_id}')

    @socketio.on('mark_all_read')
    def on_mark_all_read(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        group_id = int(data.get('group_id', 0))
        if not group_id or not FriendGroup.is_member(group_id, user_id):
            return
        GroupChat.mark_all_read(group_id, user_id)
        emit('all_read', {'group_id': group_id, 'user_id': user_id}, room=f'group_{group_id}')

    @socketio.on('delete_message')
    def on_delete(data):
        user_id = session.get('user_id')
        if not user_id:
            return
        message_id = int(data.get('message_id', 0))
        group_id = data.get('group_id')
        GroupChat.soft_delete(message_id, user_id)
        emit('message_deleted', {'message_id': message_id},
             room=f'group_{group_id}')
