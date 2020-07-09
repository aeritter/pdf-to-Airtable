from flask import Flask, render_template
from flask_socketio import SocketIO

socketio = SocketIO()

def webapp():
    app = Flask(__name__)

    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    @app.route("/")
    def home():
        return render_template('status.html')


    @app.route("/status")
    def status():
        return render_template('status.html')


    @app.route("/logs")
    def logs():
        return render_template('logs.html')


    @app.route("/settings")
    def settings():
        return render_template('settings.html')


    @app.route("/pdfsettings")
    def pdfsettings():
        return render_template('processingsettings.html')

    socketio.init_app(app)
    return app

# for testing
if __name__ == "__main__":
    socketio.run(webapp())
    print("Running!")