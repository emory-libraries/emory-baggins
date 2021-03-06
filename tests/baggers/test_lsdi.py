import os
from ConfigParser import ConfigParser
from eulxml.xmlmap import load_xmlobject_from_file
from mock import patch, Mock, call
import pytest
import tempfile
import os
import sys
import tempfile
import yaml

from baggins.baggers.lsdi import LsdiBagger, LsdiBaggee
from baggins.lsdi import digwf, fedora

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


@pytest.mark.usefixtures("capsys")
class TestLsdiBagger:

    test_config = os.path.join(FIXTURE_DIR, 'lsdi-bagger.cfg')

    @patch('baggins.baggers.lsdi.argparse')
    def test_get_options(self, mockargparse, capsys):
        mockparser = mockargparse.ArgumentParser.return_value

        mockopts = Mock(item_ids=[], gen_config=False, file=False)
        mockopts.config = self.test_config
        mockparser.parse_args.return_value = mockopts

        lbag = LsdiBagger()
        # no items specified - should exit
        with pytest.raises(SystemExit):
            lbag.get_options()

        # check captured output
        output = capsys.readouterr()
        assert output[0] == \
            'Please specify items to process\n'

        mockargparse.ArgumentParser.assert_called_once()
        mockparser.parse_args.assert_called_once()
        mockparser.print_help.assert_called_once()

        mockopts.item_ids = [3031]
        mockparser.parse_args.return_value = mockopts
        lbag.get_options()
        assert lbag.options == mockopts

    def test_load_ids_from_file(self, tmpdir, capsys):
        lbag = LsdiBagger()

        # test with nonexistent file, should error
        lbag.options.file = '/some/bogus/path/to/nonexistent/id.txt'
        # non-existent file should print an error
        lbag.load_ids_from_file()
        output = capsys.readouterr()
        assert output[0] == 'Unable to load specified id file\n'

        # generate a test file with a list of ids
        ids = ['480', '3130', '1892', '4234']
        idfile = tempfile.NamedTemporaryFile(suffix='.txt', prefix='ids-',
                                             dir=unicode(tmpdir),
                                             delete=False)
        idfile.write('\n'.join(ids))
        idfile.close()  # close to flish out to disk

        lbag.options.file = idfile.name
        loaded_item_ids = lbag.load_ids_from_file()
        for item_id in ids:
            assert item_id in loaded_item_ids

    def test_cli_options(self, capsys, tmpdir):
        lbag = LsdiBagger()

        # no item ids specified
        testargs = ["lsdi-bagger"]
        with patch.object(sys, 'argv', testargs):
            with pytest.raises(SystemExit):
                lbag.get_options()
            output = capsys.readouterr()
            assert output[0].startswith('Please specify items to process\n')

        # generate config file
        testargs = ["lsdi-bagger", "--generate-config", 'my-config-file.cfg']
        with patch.object(sys, 'argv', testargs):
            with patch.object(lbag, 'generate_configfile') as mockgen_cfg:
                # should generate config and exit
                with pytest.raises(SystemExit):
                    lbag.get_options()
                # should call generate_configfile method
                mockgen_cfg.assert_called_once()
                # no output because generate configfile is mocked

        # item ids but no output directory
        testargs = ["lsdi-bagger", "123", "456", "789"]
        with patch.object(sys, 'argv', testargs):
            with patch.object(lbag, 'load_configfile'):
                with pytest.raises(SystemExit):
                    lbag.get_options()
            output = capsys.readouterr()
            assert 'Please specify output directory' in output[0]

        # load specified config file
        test_cfgfile = os.path.join(FIXTURE_DIR, 'lsdi-bagger.cfg')
        testargs = ["lsdi-bagger", "123", "456", "-c", test_cfgfile]
        with patch.object(sys, 'argv', testargs):
            lbag.get_options()
            assert lbag.options.output == '/tmp/bags'
            assert lbag.options.digwf_url == 'http://example.co:3100/digwf_api/'

        # test that id file logic is triggered correctly by -f flag

        # empty id file input should complain about no ids to process
        empty_idfile = tempfile.NamedTemporaryFile(
            suffix='.txt', prefix='empty-ids-', dir=unicode(tmpdir),
            delete=False)
        testargs = ["lsdi-bagger", "-c", test_cfgfile,
                    '--file', empty_idfile.name]
        with patch.object(sys, 'argv', testargs):
            with pytest.raises(SystemExit):
                lbag.get_options()
                output = capsys.readouterr()
                assert 'Please specify items to process\n' in output[0]

        # valid id file
        ids = ['480', '3130', '1892', '4234']
        idfile = tempfile.NamedTemporaryFile(suffix='.txt', prefix='ids-',
                                             dir=unicode(tmpdir),
                                             delete=False)
        idfile.write('\n'.join(ids))
        idfile.close()  # close to flish out to disk
        testargs = ["lsdi-bagger", "-c", test_cfgfile, '-f', idfile.name]
        with patch.object(sys, 'argv', testargs):
            lbag.get_options()
            assert ids == lbag.options.item_ids
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
        assert cfg.has_section(lbag.fedora_cfg)
        assert cfg.has_option(lbag.fedora_cfg, 'url')

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
        assert cfg.has_section(lbag.fedora_cfg)
        assert cfg.has_option(lbag.fedora_cfg, 'url')
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
        assert lbag.options.fedora_url == 'http://server.edu:8080/fedora/'

        # if output is specified on command line, that takes precedence
        lbag.options.output = '/i/want/bags/somewhere/else'
        lbag.load_configfile()
        assert lbag.options.output != '/tmp/bags'

    def test_load_cfgfile_nonexistent(self, capsys):
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

    @patch('baggins.baggers.lsdi.Client')
    def test_process_multiple_items(self, mockdigwfclient, capsys):
        lbag = LsdiBagger()
        test_ids = [1234, 5678, 8181]
        lbag.options.item_ids = test_ids
        lbag.options.digwf_url = 'http://some.dig/wf/api'
        lbag.options.fedora_url = 'http://fed.dig:8080/fedora/'
        mockdigwf_api = mockdigwfclient.return_value
        # simuulate no matches
        mockdigwf_api.get_items.return_value.count = 0

        lbag.process_items()

        # digwf api should be called once for each item
        output = capsys.readouterr()
        for test_id in test_ids:
            assert call(item_id=test_id) in mockdigwf_api.get_items.mock_calls
            assert 'No item found for this item id %s' % test_id \
                in output[0]

    @patch('baggins.baggers.lsdi.Client')
    def test_process_items_toomany(self, mockdigwfclient, capsys):
        lbag = LsdiBagger()
        test_id = 1234
        lbag.options.item_ids = [test_id]
        lbag.options.digwf_url = 'http://some.dig/wf/api'
        mockdigwf_api = mockdigwfclient.return_value
        lbag.options.fedora_url = 'http://fed.dig:8080/fedora/'
        # simulate multiple matches
        mockdigwf_api.get_items.return_value.count = 5
        lbag.process_items()
        output = capsys.readouterr()
        assert 'Error! DigWF returned 5 matches for this item id %s' % test_id \
            in output[0]

    @patch('baggins.baggers.lsdi.Repository')
    @patch('baggins.baggers.lsdi.Client')
    @patch('baggins.baggers.lsdi.LsdiBaggee')
    def test_process_items_valid(self, mocklsdibaggee, mockdigwfclient,
                                 mockrepo, capsys):
        lbag = LsdiBagger()
        test_id = 1234
        lbag.options.item_ids = [test_id]
        lbag.options.digwf_url = 'http://some.dig/wf/api'
        lbag.options.output = '/tmp/lilbags'
        lbag.options.fedora_url = 'http://fed.dig:8080/fedora/'
        mockdigwf_api = mockdigwfclient.return_value
        # simulate one match
        mockdigwf_api.get_items.return_value.count = 1
        # set return value for mock create bag
        # NOTE: technically this returns a bagit bag; for now we are
        # just using it to display the path
        testbagpath = '/path/to/new/bag'
        mocklsdibaggee.return_value.create_bag.return_value = testbagpath

        # use mock for digwf item
        mockdigwf_item = Mock(pid='789', control_key='ocm4567',
                              marc_path='/path/to/some/ocm4567_MRC.xml')
        mockdigwf_api.get_items.return_value.items = [mockdigwf_item]
        lbag.process_items()
        mocklsdibaggee.assert_called_with(mockdigwf_item, mockrepo.return_value)
        mocklsdibaggee.return_value.create_bag.assert_called_with(lbag.options.output)

        output = capsys.readouterr()
        # currently script reports that item was found with minimal
        # metadata (NOTE: this output could change)
        assert 'Found item %s (pid %s, control key %s, marc %s)' % \
            (test_id, mockdigwf_item.pid, mockdigwf_item.control_key,
             mockdigwf_item.marc_path) in output[0]
        # and where the bag was created
        assert 'Bag created at %s' % testbagpath in output[0]


@pytest.fixture
def lsdibag():
    # create and return a LsdiBaggee object to use in tests
    digwf_item_response = os.path.join(FIXTURE_DIR, 'digwf_getitems_3031.xml')
    response = load_xmlobject_from_file(digwf_item_response, digwf.Items)
    # update path to use local fixture for marc xml
    item = response.items[0]
    item.marc_path = os.path.join(FIXTURE_DIR, 'ocm08951025_MRC.xml')
    return LsdiBaggee(response.items[0])


@pytest.mark.usefixtures("lsdibag", "tmpdir")
class TestLsdiBaggee:

    def test_object_id(self, lsdibag):
        # pid if present
        assert lsdibag.object_id() == '7svgb'
        # for item with no pid, control key should be used
        lsdibag.item.pid = None
        assert lsdibag.object_id() == 'ocm08951025'

    def test_object_title(self, lsdibag):
        # title from marc
        assert lsdibag.object_title() == \
            "Atlanta City Directory Co.'s Greater Atlanta (Georgia) city directory ... including Avondale, Buckhead ... and all immediate suburbs .."

    def test_image_files(self, lsdibag, tmpdir):
        # set fixture object to look in tmp dir
        lsdibag.item.display_image_path = unicode(tmpdir)

        # with no files to find, should error
        with pytest.raises(Exception):
            lsdibag.image_files()

        # create multiple to test precedence order
        tiffs = []
        for i in range(10):
            tiffs.append(tempfile.NamedTemporaryFile(suffix='.tif',
                                                     dir=unicode(tmpdir)))
        uc_tiffs = []
        for i in range(10):
            uc_tiffs.append(tempfile.NamedTemporaryFile(suffix='.TIF',
                                                        dir=unicode(tmpdir)))
        jp2s = []
        for i in range(10):
            jp2s.append(tempfile.NamedTemporaryFile(suffix='.jp2',
                                                    dir=unicode(tmpdir)))

        jpegs = []
        for i in range(10):
            jpegs.append(tempfile.NamedTemporaryFile(suffix='.jpg',
                                                     dir=unicode(tmpdir)))
        # count mismatch
        with pytest.raises(Exception):
            lsdibag.image_files()

        # configure fixture count to match
        lsdibag.item.display_image_count = 10
        img_files = lsdibag.image_files()
        # when *.tif is present, those should be selected
        for imgfile in tiffs:
            assert imgfile.name in img_files
            imgfile.close()  # close to delete

        # if .tif is not present, should look for .TIF
        img_files = lsdibag.image_files()
        for imgfile in uc_tiffs:
            assert imgfile.name in img_files
            imgfile.close()   # close to delete

        # if .tif/.TIF is not present, should look for .jp2
        img_files = lsdibag.image_files()
        for imgfile in jp2s:
            assert imgfile.name in img_files
            imgfile.close()   # close to delete

        # if nothing else is found, should look for .jpeg
        img_files = lsdibag.image_files()
        for imgfile in jpegs:
            assert imgfile.name in img_files
            imgfile.close()   # close to delete

    def test_page_text_files(self, lsdibag, tmpdir):
        # set fixture object to look in tmp dir
        lsdibag.item.ocr_file_path = unicode(tmpdir)

        # with no files to find, should error
        with pytest.raises(Exception):
            lsdibag.page_text_files()

        # generate test text files
        textfiles = []
        for _ in range(10):
            textfiles.append(tempfile.NamedTemporaryFile(suffix='.txt',
                                                         dir=unicode(tmpdir)))
        # without .pos files, should still error
        with pytest.raises(Exception):
            lsdibag.page_text_files()

        # generate test position files
        posfiles = []
        for _ in range(10):
            posfiles.append(tempfile.NamedTemporaryFile(suffix='.pos',
                                                        dir=unicode(tmpdir)))
        # count mismatch should error
        with pytest.raises(Exception):
            lsdibag.page_text_files()

        lsdibag.item.ocr_file_count = 10
        files = lsdibag.page_text_files()
        # should include all txt and pos files
        for textfile in textfiles:
            assert textfile.name in files
        for posfile in posfiles:
            assert posfile.name in files

    def test_data_files(self, lsdibag):
        with patch.object(lsdibag, 'image_files') as mock_imgfiles:
            with patch.object(lsdibag, 'page_text_files') as mock_txtfiles:

                mock_imgfiles.return_value = [
                    '001.tif', '002.tif', '003.tif'
                ]
                mock_txtfiles.return_value = [
                    '001.txt', '002.txt', '003.txt'
                    '001.pos', '002.pos', '003.pos'
                ]

                datafiles = lsdibag.data_files()

                # should include pdf and ocr file
                assert lsdibag.item.pdf in datafiles
                assert lsdibag.item.ocr_file in datafiles
                # should all image and text files
                for imgfile in mock_imgfiles.return_value:
                    assert imgfile in datafiles
                for txtfile in mock_txtfiles.return_value:
                    assert txtfile in datafiles

    def test_bag_info(self, lsdibag):
        # should lookup based on fixture item collection
        info = lsdibag.bag_info()
        assert info['Source-Organization'] == 'undetermined'
        assert info['Organization-Address'] == 'not known'

        # set item collection id to one that can be looked up
        lsdibag.item.collection_id = 21
        info = lsdibag.bag_info()
        assert info['Source-Organization'] == 'Stuart A. Rose Manuscript, Archives and Rare Book Library'
        assert info['Organization-Address'] == '540 Asbury Circle, Atlanta, GA 30322'

    # TODO: test process_items method; current functionality is just
    # placeholder logic and will change

    def test_descriptive_metadata(self, lsdibag):
        assert lsdibag.item.marc_path in lsdibag.descriptive_metadata()

    def test_content_metadata(self,lsdibag):
        print "passing"

    def test_relationship_metadata(self, lsdibag):
        # use mock for fedora repo object
        mockrepo = Mock()
        lsdibag.repo = mockrepo
        mockvol = mockrepo.get_object.return_value
        # simulate pid present but no object in fedora
        mockvol.exists = False

        rel_info = lsdibag.relationship_metadata_info()
        mockrepo.get_object.assert_called_with('emory:%s' % lsdibag.item.pid,
                                               type=fedora.Volume)
        assert rel_info['DigWF Collection']['id'] == 10
        assert rel_info['DigWF Collection']['name'] == 'Atlanta City Directories'

        # simulate actual objects
        mockvol.exists = True
        mockvol.book.pid = 'book:1'
        mockvol.book.ark_uri = 'http:/pid.co/ark:/1234/56'
        mockvol.book.ark = 'ark:/1234/56'
        mockvol.book.label = 'ocm12345'
        mockvol.book.collection.pid = 'coll:1'
        mockvol.book.collection.ark_uri = 'http:/pid.co/ark:/1234/78'
        mockvol.book.collection.ark = 'ark:/1234/78'
        mockvol.book.collection.label = 'Collection foo'

        rel_info = lsdibag.relationship_metadata_info()
        assert rel_info['Fedora Book']['pid'] == mockvol.book.pid
        assert rel_info['Fedora Book']['ark'] == mockvol.book.ark
        assert rel_info['Fedora Book']['ark_uri'] == mockvol.book.ark_uri
        assert rel_info['Fedora Book']['name'] == mockvol.book.label

        assert rel_info['Fedora Collection']['pid'] == mockvol.book.collection.pid
        assert rel_info['Fedora Collection']['ark'] == mockvol.book.collection.ark
        assert rel_info['Fedora Collection']['ark_uri'] == mockvol.book.collection.ark_uri
        assert rel_info['Fedora Collection']['name'] == mockvol.book.collection.label

        # no pid, doesn't try to do fedora lookup
        lsdibag.item.pid = None
        mockrepo.get_object.reset_mock()
        lsdibag.relationship_metadata_info()
        mockrepo.get_object.assert_not_called()

    def test_add_relationship_metadata(self, lsdibag, tmpdir):
        faux_rels = {'book': {'id': 'foo'}}
        with patch.object(lsdibag, 'relationship_metadata_info') as mockrel:
            mockrel.return_value = faux_rels
            lsdibag.add_relationship_metadata(unicode(tmpdir))

        # file should have been created where expected
        expected_path = os.path.join(unicode(tmpdir), 'metadata',
                                     'relationship',
                                     'machine-relationship.txt')
        assert os.path.exists(expected_path)

        with open(expected_path) as rels_file:
            data = yaml.load(rels_file)

        assert data == faux_rels
