from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db/kanban'
    app.config['SECRET_KEY'] = 'your_secret_key'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    # Error handler for 404
    @app.errorhandler(404)
    def page_not_found(e):
        return redirect(url_for('main.login'))

    return app
