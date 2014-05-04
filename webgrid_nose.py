import os
from os import path as osp
from sys import argv

import nose

package_dir = osp.dirname(__file__)
tests_dir = osp.join(package_dir, 'webgrid', 'tests')


def run_nose():
    nose.main(argv, defaultTest=tests_dir)


class WebGridNosePlugin(nose.plugins.Plugin):
    enabled = False

    def configure(self, options, config):
        """Configure the plugin"""
        curdir = osp.realpath(os.curdir)
        if curdir.startswith(package_dir):
            self.enabled = True

    def begin(self):
        from webgrid_ta.app import create_app
        app = create_app(config='Test')
        app.test_request_context().push()

        from webgrid_ta.model import load_db
        load_db()
