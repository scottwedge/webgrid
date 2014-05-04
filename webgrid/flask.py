from __future__ import absolute_import
from flask import request, session, flash, Blueprint


class FlaskSQLAlchemyManager(object):

    def __init__(self, db=None):
        self.db = db

    def init_db(self, db):
        self.db = db

    def sa_query(self, *args, **kwargs):
        return self.db.session.query(*args, **kwargs)

    def request_args(self):
        return request.args

    def web_session(self):
        return session

    def flash_message(self, category, message):
        flash(message, category)

    def request(self):
        return request

    def static_url(self, url_tail):
        return '/static/' + url_tail

webgrid = Blueprint('webgrid', __name__, static_folder='static', static_url_path='/webgrid')
