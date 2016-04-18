from __future__ import absolute_import
import warnings

from flask import Flask
from flask.ext.bootstrap import Bootstrap

from webgrid.flask import WebGrid

# ignore warning about Decimal lossy conversion with SQLite from SA
warnings.filterwarnings('ignore', '.*support Decimal objects natively.*')

webgrid = WebGrid()


def create_app(config):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # app.config['SQLALCHEMY_ECHO'] = True
    # app.config['DEBUG'] = True
    if config == 'Test':
        app.config['TEST'] = True
    app.secret_key = 'only-testing'

    from webgrid_ta.model import db
    db.init_app(app)
    webgrid.init_db(db)
    Bootstrap(app)
    webgrid.init_app(app)

    from .views import main
    app.register_blueprint(main)

    return app
