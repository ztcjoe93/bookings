from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb

login_manager = LoginManager()
login_manager.login_view = 'main_panel.login'
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
breadcrumb = Breadcrumbs()
