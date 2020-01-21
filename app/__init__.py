import logging
import sys
from flask import Flask, render_template
from .admin import admin_routes
from .main import main_routes

from app.extensions import (
	login_manager,
	db,
	migrate,
        mail
)

login_manager.login_view = 'main_panel.login'

def create_app(config_object="app.settings"):
    app = Flask(__name__, static_url_path='/static')
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    
    return app

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    return None

def register_blueprints(app):
    app.register_blueprint(admin_routes.admin_panel)
    app.register_blueprint(main_routes.main_panel)

def register_errorhandlers(app):
    def render_error(error):
        error_code = getattr(error, "code", 500)
        return render_template(f"{error_code}.html"), error_code

    for errcode in [401, 403, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None
