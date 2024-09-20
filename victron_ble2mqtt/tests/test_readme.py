from cli_base.cli_tools.test_utils.assertion import assert_in
from cli_base.cli_tools.test_utils.cli_readme import AssertCliHelpInReadme
from cli_base.cli_tools.test_utils.rich_test_utils import (
    assert_no_color_env,
    assert_rich_click_no_color,
    assert_rich_no_color,
    assert_subprocess_rich_diagnose_no_color,
)
from cli_base.toml_settings.test_utils.cli_mock import TomlSettingsCliMock
from ha_services.cli_app.settings import SETTINGS_DIR_NAME, SETTINGS_FILE_NAME
from ha_services.example import DemoSettings
from manageprojects.tests.base import BaseTestCase

from victron_ble2mqtt import constants
from victron_ble2mqtt.cli_dev import PACKAGE_ROOT


TERM_WIDTH = 100


class ReadmeTestCase(BaseTestCase):
    cli_mock = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        settings_overwrites = dict(
            systemd=dict(
                template_context=dict(
                    user='MockedUserName',
                    group='MockedUserName',
                )
            ),
        )

        cls.cli_mock = TomlSettingsCliMock(
            SettingsDataclass=DemoSettings,
            settings_overwrites=settings_overwrites,
            dir_name=SETTINGS_DIR_NAME,
            file_name=SETTINGS_FILE_NAME,
            width=TERM_WIDTH,
        )
        cls.cli_mock.__enter__()

        cls.readme_assert = AssertCliHelpInReadme(base_path=PACKAGE_ROOT, cli_epilog=constants.CLI_EPILOG)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.cli_mock.__exit__(None, None, None)

    def test_cli_mock(self):
        assert_no_color_env(width=TERM_WIDTH)
        assert_subprocess_rich_diagnose_no_color(width=TERM_WIDTH)
        assert_rich_no_color(width=TERM_WIDTH)
        assert_rich_click_no_color(width=TERM_WIDTH)

    def invoke_cli(self, *args):
        return self.cli_mock.invoke(cli_bin=PACKAGE_ROOT / 'cli.py', args=args, strip_line_prefix='Usage: ')

    def invoke_dev_cli(self, *args):
        return self.cli_mock.invoke(cli_bin=PACKAGE_ROOT / 'dev-cli.py', args=args, strip_line_prefix='Usage: ')

    def test_main_help(self):
        stdout = self.invoke_cli('--help')
        assert_in(
            content=stdout,
            parts=(
                'Usage: ./cli.py [OPTIONS] COMMAND [ARGS]...',
                'edit-settings',
                'publish-loop',
                constants.CLI_EPILOG,
            ),
        )
        self.readme_assert.assert_block(text_block=stdout, marker='app help')

    def test_dev_help(self):
        stdout = self.invoke_dev_cli('--help')
        assert_in(
            content=stdout,
            parts=(
                'Usage: ./dev-cli.py [OPTIONS] COMMAND [ARGS]...',
                'fix-code-style',
                'tox',
                constants.CLI_EPILOG,
            ),
        )
        self.readme_assert.assert_block(text_block=stdout, marker='dev help')
