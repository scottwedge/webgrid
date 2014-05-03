from os import path as osp
from sys import argv

import nose

tests_dir = osp.join(osp.dirname(__file__), 'webgrid', 'tests')


def run_nose():
    nose.main(argv, defaultTest=tests_dir)


class InitAppPlugin(nose.plugins.Plugin):
    enabled = True

    def configure(self, options, config):
        """Configure the plugin"""
        self.enabled = True

    def begin(self):
        print 'starting'
        from webgrid_ta.app import create_app
        app = create_app(config='Test')
        app.test_request_context().push()

        from webgrid_ta.model import load_db
        load_db()
