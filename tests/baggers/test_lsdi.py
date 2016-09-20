from mock import patch, Mock

from baggins.baggers.lsdi import LsdiBagger


class TestLsdiBagger:

    @patch('baggins.baggers.lsdi.exit')
    @patch('baggins.baggers.lsdi.argparse')
    def test_get_options(self, mockargparse, mockexit):
        mockparser = mockargparse.ArgumentParser.return_value

        mockparser.parse_args.return_value = Mock(item_ids=[])
        # parser = argparse.ArgumentParser(
        #     description='Generate bagit bags from LSDI digitized book content')
        # parser.add_argument('item_ids', metavar='ID', nargs='*',
        #                     help='Digitization Workflow Item ID')
        # self.options = parser.parse_args()

        lbag = LsdiBagger()
        # no items specified
        lbag.get_options()
        mockargparse.ArgumentParser.assert_called_once()
        mockparser.parse_args.assert_called_once()
        mockparser.print_help.assert_called_once()
        mockexit.assert_called_once()

        mockexit.reset_mock()
        mockoptions = Mock(item_ids=[3031])
        mockparser.parse_args.return_value = mockoptions
        lbag.get_options()
        mockexit.assert_not_called()
        assert lbag.options == mockoptions


    # TODO: test process_items method; current functionality is just
    # placeholder logic and will change
