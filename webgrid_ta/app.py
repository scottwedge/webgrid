import warnings

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from webgrid.flask import FlaskSQLAlchemyManager, webgrid

# ignore warning about Decimal lossy conversion with SQLite from SA
warnings.filterwarnings('ignore', '.*support Decimal objects natively.*')

fsam = FlaskSQLAlchemyManager()

def create_app(config):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/webgrid.db'
    #app.config['SQLALCHEMY_ECHO'] = True
    #app.config['DEBUG'] = True
    if config == 'Test':
        app.config['TEST'] = True
    app.secret_key = 'only-testing'

    from webgrid_ta.model import db
    db.init_app(app)
    fsam.init_db(db)
    Bootstrap(app)
    app.register_blueprint(webgrid)

    from .views import main
    app.register_blueprint(main)

    return app


