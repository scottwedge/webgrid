from __future__ import absolute_import

from blazeweb.content import getcontent
from blazeweb.globals import rg, user
from blazeweb.routing import abs_static_url
from blazeweb.utils import abort
from blazeweb.wrappers import StreamResponse
from sqlalchemybwc import db as sabwc_db
from webgrid import BaseGrid


class WebGrid(object):

    def __init__(self, db=None):
        self.init_db(db or sabwc_db)

    def init_db(self, db):
        self.db = db

    def sa_query(self, *args, **kwargs):
        return self.db.sess.query(*args, **kwargs)

    def request_args(self):
        return rg.request.args

    def web_session(self):
        return user

    def flash_message(self, category, message):
        user.add_message(category, message)

    def request(self):
        return rg.request

    def static_url(self, url_tail):
        return abs_static_url('component/webgrid/{0}'.format(url_tail))

    def xls_as_response(self, wb, file_name):
        rp = StreamResponse()
        rp.headers['Content-Type'] = 'application/vnd.ms-excel'
        rp.headers['Content-Disposition'] = 'attachment; filename={0}'.format(file_name)
        wb.save(rp.stream)
        abort(rp)

    def render_template(self, endpoint, **kwargs):
        return getcontent(endpoint, **kwargs)


class Grid(BaseGrid):
    manager = WebGrid()
