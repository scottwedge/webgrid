from __future__ import absolute_import

from os import path

from blazeweb.content import getcontent
from blazeweb.globals import ag, rg, user
from blazeweb.routing import abs_static_url
from blazeweb.templating.jinja import content_filter
from blazeweb.utils import abort
from blazeweb.wrappers import StreamResponse
from jinja2.exceptions import TemplateNotFound
from sqlalchemybwc import db as sabwc_db
from webgrid import BaseGrid


class WebGrid(object):

    def __init__(self, db=None, component='webgrid'):
        self.init_db(db or sabwc_db)
        self.component = component
        ag.tplengine.env.filters['wg_safe'] = content_filter

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

    def static_path(self):
        return path.join(path.dirname(__file__), 'static')

    def static_url(self, url_tail):
        return abs_static_url('component/webgrid/{0}'.format(url_tail))

    def xls_as_response(self, wb, file_name):
        rp = StreamResponse()
        rp.headers['Content-Type'] = 'application/vnd.ms-excel'
        rp.headers['Content-Disposition'] = 'attachment; filename={0}'.format(file_name)
        wb.save(rp.stream)
        abort(rp)

    def render_template(self, endpoint, **kwargs):
        try:
            return getcontent(endpoint, **kwargs)
        except TemplateNotFound:
            if ':' in endpoint:
                raise
            return getcontent('{0}:{1}'.format(self.component, endpoint), **kwargs)
wg_blaze_manager = WebGrid()


class Grid(BaseGrid):
    manager = wg_blaze_manager
