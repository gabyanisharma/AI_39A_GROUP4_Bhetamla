import os
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'Bhetamla is starting on http://127.0.0.1:{port}')
    # use_reloader=False: avoids the APScheduler background jobs being
    # started twice (once in the reloader parent and once in the child).
    socketio.run(app, debug=True, host='127.0.0.1', port=port, use_reloader=False, allow_unsafe_werkzeug=True)

