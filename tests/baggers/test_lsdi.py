from mock import patch, Mock
import pytest

from baggins.baggers.lsdi import LsdiBagger


class TestLsdiBagger:

    @patch('baggins.baggers.lsdi.argparse')
    def test_get_options(self, mockargparse):
        mockparser = mockargparse.ArgumentParser.return_value

        mockparser.parse_args.return_value = Mock(item_ids=[])
        # parser = argparse.ArgumentParser(
        #     description='Generate bagit bags from LSDI digitized book content')
        # parser.add_argument('item_ids', metavar='ID', nargs='*',
        #                     help='Digitization Workflow Item ID')
        # self.options = parser.parse_args()

        lbag = LsdiBagger()
        # no items specified - should exit
        with pytest.raises(SystemExit):
            lbag.get_options()
        mockargparse.ArgumentParser.assert_called_once()
        mockparser.parse_args.assert_called_once()
        mockparser.print_help.assert_called_once()

        mockoptions = Mock(item_ids=[3031])
        mockparser.parse_args.return_value = mockoptions
        lbag.get_options()
        assert lbag.options == mockoptions

    # TODO: test process_items method; current functionality is just
    # placeholder logic and will change
