from bx_py_utils.test_utils.unittest_utils import BaseDocTests

import victron_ble2mqtt


class DocTests(BaseDocTests):
    def test_doctests(self):
        self.run_doctests(
            modules=(victron_ble2mqtt,),
        )
