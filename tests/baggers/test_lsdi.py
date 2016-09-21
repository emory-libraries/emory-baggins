from ConfigParser import ConfigParser
from mock import patch, Mock
import pytest
import os
import tempfile

from baggins.baggers.lsdi import LsdiBagger


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@pytest.mark.usefixtures("capsys")
class TestLsdiBagger:

    test_config = os.path.join(FIXTURE_DIR, 'lsdi-bagger.cfg')

    @patch('baggins.baggers.lsdi.argparse')
    def test_get_options(self, mockargparse, capsys):
        mockparser = mockargparse.ArgumentParser.return_value

        mockopts = Mock(item_ids=[], gen_config=False)
        mockopts.config = self.test_config
        mockparser.parse_args.return_value = mockopts

        lbag = LsdiBagger()
        # no items specified - should exit
        with pytest.raises(SystemExit):
            lbag.get_options()

        # check captured output
        output = capsys.readouterr()
        assert output[0] == \
            'Please specify one or more item ids for items to process\n'

        mockargparse.ArgumentParser.assert_called_once()
        mockparser.parse_args.assert_called_once()
        mockparser.print_help.assert_called_once()

        mockopts.item_ids = [3031]
        mockparser.parse_args.return_value = mockopts
        lbag.get_options()
        assert lbag.options == mockopts

    # tests for config parser logic (creation, loading, etc)

    def test_setup_configparser(self):
        lbag = LsdiBagger()
        lbag.options = Mock()
        cfg = lbag.setup_configparser()
        assert isinstance(cfg, ConfigParser)
        assert cfg.has_section(lbag.digwf_cfg)
        assert cfg.has_option(lbag.digwf_cfg, 'url')
        assert cfg.has_section(lbag.filepaths_cfg)
        assert cfg.has_option(lbag.filepaths_cfg, 'output')
        # NOTE: more sections will probably be added and should be tested
        # when they are

    def test_generate_configfile(self, capsys):
        lbag = LsdiBagger()
        tempconfig = tempfile.NamedTemporaryFile()
        lbag.options = Mock(gen_config=tempconfig.name, output=None)
        lbag.generate_configfile()
        # check captured output
        output = capsys.readouterr()
        assert output[0] == \
            'Config file created at %s\n' % tempconfig.name

        cfg = ConfigParser()
        cfg.readfp(tempconfig)
        assert cfg.has_section(lbag.digwf_cfg)
        assert cfg.has_option(lbag.digwf_cfg, 'url')
        assert cfg.has_section(lbag.filepaths_cfg)
        assert cfg.has_option(lbag.filepaths_cfg, 'output')
        # no output option specified - empty string
        assert cfg.get(lbag.filepaths_cfg, 'output') == ''

        # output dir should prepopulate if set in options
        output_dir = '/tmp/baggins/'
        tempconfig = tempfile.NamedTemporaryFile()
        lbag.options = Mock(gen_config=tempconfig.name, output=output_dir)
        lbag.generate_configfile()
        cfg.readfp(tempconfig)
        # output option specified, passed through to config
        assert cfg.get(lbag.filepaths_cfg, 'output') == output_dir

    def test_load_configfile_valid(self):
        lbag = LsdiBagger()
        # use a Mock to simulate argparse options
        lbag.options = Mock(item_ids=[], gen_config=False, digwf_url=None,
                            output=None)
        # load fixture that should work
        lbag.options.config = os.path.join(FIXTURE_DIR, 'lsdi-bagger.cfg')
        lbag.load_configfile()
        # value from the config fixture
        assert lbag.options.digwf_url == 'http://example.co:3100/digwf_api/'
        assert lbag.options.output == '/tmp/bags'

        # if output is specified on command line, that takes precedence
        lbag.options.output = '/i/want/bags/somewhere/else'
        lbag.load_configfile()
        assert lbag.options.output != '/tmp/bags'

    def test_load_configfile_nonexistent(self, capsys):
        lbag = LsdiBagger()
        # use a Mock to simulate argparse options
        lbag.options = Mock(item_ids=[], gen_config=False, digwf_url=None)

        # nonexistent file
        bad_cfg_path = '/not/really/here'
        lbag.options.config = bad_cfg_path
        with pytest.raises(SystemExit):
            lbag.load_configfile()

        output = capsys.readouterr()
        assert output[0] == \
            'Unable to load config file at %s\n' % bad_cfg_path + \
            'Please generate or specify a config file.\n'

    def test_load_configfile_empty(self, capsys):
        lbag = LsdiBagger()
        # use a Mock to simulate argparse options
        lbag.options = Mock(item_ids=[], gen_config=False, digwf_url=None)

        # empty file
        empty_cfg = tempfile.NamedTemporaryFile()
        lbag.options.config = empty_cfg.name
        with pytest.raises(SystemExit):
            lbag.load_configfile()

        output = capsys.readouterr()
        assert output[0] == \
            'Error: Digitization Workflow URL not configured\n'

    # TODO: test process_items method; current functionality is just
    # placeholder logic and will change
