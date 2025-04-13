from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config.from_object('config.Config')
    CORS(app)
    db.init_app(app)

    from blog import routes
    app.register_blueprint(routes.bp)

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    return app