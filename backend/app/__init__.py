"""Flask app factory.

Flask is imported lazily inside create_app so that the pure-Python packages
app.core, app.quantum and app.classical can be imported (and tested) without
Flask or a database being present.
"""


def create_app(config_object=None):
    from flask import Flask
    from flask_cors import CORS

    from .config import Config
    from .extensions import db, migrate

    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    CORS(app, origins=app.config["CORS_ORIGINS"].split(","))
    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401  (register tables)
    from .routes import register_routes

    register_routes(app)
    return app
