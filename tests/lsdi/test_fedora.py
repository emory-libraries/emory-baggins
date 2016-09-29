from mock import Mock

from baggins.lsdi.fedora import ArkDigitalObject


class TestArkDigitalObject:

    def test_ark_uri(self):
        # use mock in place of real fedora api
        arkobj = ArkDigitalObject(Mock())
        # no identifier
        assert arkobj.ark_uri == None

        ark_uri = 'http://pid.co/ark:/1234/98'
        arkobj.dc.content.identifier_list.append(ark_uri)
        # cached property, should still be None
        assert arkobj.ark_uri == None

        arkobj = ArkDigitalObject(Mock())
        arkobj.dc.content.identifier_list.append(ark_uri)
        assert arkobj.ark_uri == ark_uri

        arkobj = ArkDigitalObject(Mock())
        arkobj.dc.content.identifier_list.append('pid:foo')
        arkobj.dc.content.identifier_list.append(25)
        arkobj.dc.content.identifier_list.append(ark_uri)
        assert arkobj.ark_uri == ark_uri

    def test_ark(self):
        arkobj = ArkDigitalObject(Mock())
        # no identifier
        assert arkobj.ark == None

        arkobj = ArkDigitalObject(Mock())
        ark = 'ark:/1234/98'
        ark_uri = 'http://pid.co/%s' % ark
        arkobj.dc.content.identifier_list.append(ark_uri)
        # cached property, should still be None
        assert arkobj.ark == ark

