import os
from eulxml.xmlmap import load_xmlobject_from_file
from baggins.lsdi import mets

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


class TestMets:

    mets_response = os.path.join(FIXTURE_DIR, 'test.mets.xml')
    empty_response = os.path.join(FIXTURE_DIR, 'test.mets_nomatch.xml')

    def test_mets(self):
    	response = load_xmlobject_from_file(self.mets_response, mets.Mets)
    	print response.create_tiffs
    	assert response == 1
