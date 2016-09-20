from mock import patch, Mock
import pytest
import os

from baggins.baggers.lsdi import LsdiBagger


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


class TestLsdiBagger:

    test_config = os.path.join(FIXTURE_DIR, 'lsdi-bagger.cfg')

    @patch('baggins.baggers.lsdi.argparse')
    def test_get_options(self, mockargparse):
        mockparser = mockargparse.ArgumentParser.return_value

        mockopts = Mock(item_ids=[], gen_config=False)
        mockopts.config = self.test_config
        mockparser.parse_args.return_value = mockopts

        lbag = LsdiBagger()
        # no items specified - should exit
        with pytest.raises(SystemExit):
            lbag.get_options()
        mockargparse.ArgumentParser.assert_called_once()
        mockparser.parse_args.assert_called_once()
        mockparser.print_help.assert_called_once()

        mockopts.item_ids = [3031]
        mockparser.parse_args.return_value = mockopts
        lbag.get_options()
        assert lbag.options == mockopts

    # TODO: test generate config file, loading config file

    # TODO: test process_items method; current functionality is just
    # placeholder logic and will change
