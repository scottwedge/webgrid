from __future__ import absolute_import

from io import BytesIO
from os import path

from flask import request, session, flash, Blueprint, url_for, send_file


class WebGrid(object):

    def __init__(self, db=None):
        self.init_db(db)

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

    def static_path(self):
        return path.join(path.dirname(__file__), 'static')

    def static_url(self, url_tail):
        return url_for('webgrid.static', filename=url_tail)

    def init_app(self, app):
        bp = Blueprint(
            'webgrid',
            __name__,
            static_folder='static',
            static_url_path=app.static_url_path + '/webgrid'
        )
        app.register_blueprint(bp)

    def xls_as_response(self, workbook, filename):
        buf = BytesIO()
        workbook.save(buf)
        buf.seek(0)
        return send_file(buf, mimetype='application/vnd.ms-excel',
                         as_attachment=True, attachment_filename=filename)
