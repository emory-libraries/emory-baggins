import bagit
import filecmp
import os
import pytest
import tempfile

from baggins.baggers.bag import Baggee


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')

# extend with test subclasses, to test functionality

class SampleBaggee(Baggee):

    pid = '1234'
    title = 'A Test Item to Bag'
    files = None
    desc_metadata = None

    def __init__(self):
        self.files = []
        self.desc_metadata = []
        self.bag_info = {}

    def bag_info(self):
        return self.bag_info

    def data_files(self):
        return self.files

    def descriptive_metadata(self):
        return self.desc_metadata


@pytest.mark.usefixtures("tmpdir")
class TestBaggee:

    marcml_basename = 'ocm08951025_MRC.xml'
    marcxml_file = os.path.join(FIXTURE_DIR, marcml_basename)


    def test_object_id(self):
        assert Baggee().object_id() == None
        assert SampleBaggee().object_id() == SampleBaggee.pid

    def test_object_id(self):
        assert Baggee().object_title() == None
        assert SampleBaggee().object_title() == SampleBaggee.title

    def test_file_title(self):
        samplebag = SampleBaggee()
        # basic slugifcation from object title
        assert samplebag.file_title() == 'A-Test-Item-to-Bag'
        # test truncation
        samplebag.title = 'A Test Item to Bag with a very long title'
        assert samplebag.file_title() == 'A-Test-Item-to-Bag-with-a-very'
        # partial word after truncation should be included
        samplebag.title = 'A Test Item with a very long title'
        assert samplebag.file_title() == 'A-Test-Item-with-a-very-long-title'

    def test_bag_name(self):
        assert SampleBaggee().bag_name() == '1234-A-Test-Item-to-Bag'

    def test_add_data_files(self, tmpdir):
        samplebag = SampleBaggee()
        # create a temporary file to act as data payload
        samplecontent = tempfile.NamedTemporaryFile()
        samplebag.files.append(samplecontent.name)
        samplebag.add_data_files(unicode(tmpdir))
        samplecontent_basename = os.path.basename(samplecontent.name)
        # check that temp file was copied where we expect it to be
        filecmp.cmp(samplecontent.name,
                    os.path.join(unicode(tmpdir), samplecontent_basename))

    def test_add_descriptive_metadata(self, tmpdir):
        samplebag = SampleBaggee()
        samplebag.desc_metadata.append(self.marcxml_file)

        samplebag.add_descriptive_metadata(unicode(tmpdir))
        filecmp.cmp(self.marcxml_file,
                    os.path.join(unicode(tmpdir), 'metadata', 'descriptive',
                                 self.marcml_basename))

    def test_create_bag(self, tmpdir):
        samplebag = SampleBaggee()
        # create a temporary file to act as data payload
        samplecontent = tempfile.NamedTemporaryFile()
        samplebag.files.append(samplecontent.name)
        samplecontent_basename = os.path.basename(samplecontent.name)
        # add descriptive metadata
        samplebag.desc_metadata.append(self.marcxml_file)
        bag = samplebag.create_bag(unicode(tmpdir))
        assert isinstance(bag, bagit.Bag)

        expected_bagdir = os.path.join(unicode(tmpdir), samplebag.bag_name())
        assert os.path.isdir(expected_bagdir)

        # load as a bag to inspect
        bag = bagit.Bag(expected_bagdir)
        # should be a valid bag
        assert bag.is_valid()
        # should include test data file
        payload_files = list(bag.payload_files())
        assert 'data/%s' % samplecontent_basename in payload_files

        # should include metadata
        # - descriptive metadata
        assert 'data/metadata/descriptive/%s' % self.marcml_basename \
            in payload_files

        # bagit handles these automatically, but explicitly check that they
        # are set in our bags
        assert bag.version
        assert bag.encoding

        # by default, we want to create both md5 and sha256 manifests
        manifest_names = [os.path.basename(manifest)
                          for manifest in bag.manifest_files()]
        # NOTE: could base this test on samplebag.checksum_algorithms
        assert 'manifest-md5.txt' in manifest_names
        assert 'manifest-sha256.txt' in manifest_names
