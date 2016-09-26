import bagit
import os
import shutil
from slugify import slugify


class Baggee(object):
    '''Base class for an item to be bagged.

    Extending classes will most likely want to override :meth:`object_id`,
    :meth:`object_title`, and :meth:`data_files`.

    '''

    #: rough title length, for truncating long titles
    title_length = 30

    #: checksum algorithms to use when generating the bag
    checksum_algorithms = ['md5', 'sha256']
    # NOTE: may eventually want to make these configurable

    def object_id(self):
        '''Object ID for this item. Use PID, ARK, or OCLC Number
        in that order of preference.

        Default implemntation: returns `pid` attribute on the current object
        if it exists.'''
        if getattr(self, 'pid', None):
            return getattr(self, 'pid')

    def object_title(self):
        '''Object title.  For items with MARC records, use 245$a.

        Default implementation: returns 'title' attribute on the current
        object if it exists.
        '''
        if getattr(self, 'title', None):
            return getattr(self, 'title')

    def data_files(self):
        '''List of files to be included in the bag as payload content.'''
        return []

    def descriptive_metadata(self):
        '''List of files to be included in the bag as descriptive metadata
         content.'''
        return []

    # internal methods that probably shouldn't be extended for most
    # use cases

    def file_title(self):
        '''Convert object title to a format for use in the bag filename.
        Name is slugified, and then truncated to :attr:`title_length`
        and expanded as necessary to complete the current word.
        '''
        # slugify the object title, then truncate,
        # then truncate to last word based on - delimiter
        title = slugify(self.object_title())
        # NOTE: this slugify doesn't not lowercase letters;
        # do we want to add that?

        # if the title is longer than requested length, truncate
        # to nearest complete word
        if len(title) > self.title_length:
            # truncated title
            truncated_title = title[:self.title_length]
            # If truncated title ends with '-', then it already ends with
            # a complete word. Remove the last - and return.
            if truncated_title[-1] == '-':
                return truncated_title[:-1]
            # use extra title content after length to complete a partial word
            extra = title[self.title_length:]
            # title up to end of first word after title length
            extra_index = extra.find('-')
            # if no `-` was found, then truncated portion is the end of the
            # last word in the title.  Weturn the whole title.
            if extra_index == -1:
                return title
            # otherwise, truncate to first complete word
            return title[:self.title_length + extra_index]
        return title

    def bag_name(self):
        '''Name of the bag to be created, in  the form
        objectid-objectname.'''
        return '%s-%s' % (self.object_id(), self.file_title())

    def add_data_files(self, bagdir):
        '''Copy data files into the bag staging directory.'''
        for datafile in self.data_files():
            # use copy2 to preserve original file statistics
            shutil.copy2(datafile, bagdir)
            datafile_base = os.path.basename(datafile)
            # make sure file is writable so bagit can move it,
            # otherwise bagit will error
            # NOTE: for now, assuming user creating the bag has at least
            # group permissions on the content being bagged; might
            # need revision at a later point.
            os.chmod(os.path.join(bagdir, datafile_base), 0664)

    def add_descriptive_metadata(self, bagdir):
        metadata_dir = os.path.join(bagdir, 'metadata', 'descriptive')
        os.makedirs(metadata_dir)
        for mdata_file in self.descriptive_metadata():
            shutil.copy2(mdata_file, metadata_dir)
            # perms possibly not needed for metadata, since bagit
            # doesn't have to move it
            # mdata_base = os.path.basename(mdata_file)
            # os.chmod(os.path.join(metadata_dir, mdata_base), 0664)

    def create_bag(self, basedir):
        '''Create a bagit bag for this item.'''
        bagdir = os.path.join(basedir, self.bag_name())
        os.mkdir(bagdir)

        # add payload  data to the bag
        self.add_data_files(bagdir)

        # ** add metadata **

        # NOTE: emory bagit spec calls for metadata content to be
        # included as "tag" files outside of the data directory, but
        # python-bagit doesn't currently support generating tag manifests
        # for optional tag files in subdirectories.  For details, see
        # https://github.com/LibraryOfCongress/bagit-python/issues/68
        # for the discussion and
        # https://github.com/LibraryOfCongress/bagit-python/pull/69
        # for the fix.  Once a new release is available with the fix,
        # we should require that minimu version and update the logic here

        # descriptive metadata
        self.add_descriptive_metadata(bagdir)

        # create the bag
        bag = bagit.make_bag(bagdir, checksum=self.checksum_algorithms)

        # NOTE: to add metadata as tag files (once there is a version of
        # python-bagit that supports it), add the tagfile content to the
        # bag directories here, and then re-save the bag, which should
        # update the tag-manifests appropriately.  (Also update unit
        # tests to check that the manifests are generated as expected.)

        return bag

class BagInfo(Baggee):

    def source_organization(self):
        '''Object source organization for the bag'''

        # where do we get source organization from XML or external file?
        return self.item.source_organization()

    def source_organization_address(self):
        '''Object source organization address for the bag'''

        # where do we get source organization address from XML or external file?
        return self.item.source_organization_address()

    def contact_name(self):
        '''Object contact name for the bag'''

        # where do we get contact name from XML or external file?
        return self.item.contact_name()

    
    def contact_phone(self):
        '''Object contact phone for the bag'''

        # where do we get contact phone from XML or external file?
        return self.item.contact_name()

    def contact_email(self):
        '''Object contact phone for the bag'''

        # where do we get contact phone from XML or external file?
        return self.item.contact_email()

    def external_description(self):
        '''Object external description for the bag: use description from MARC xml'''

        return self.item.external_description()

    def external_identifier(self):
        '''Object external identifier for the bag: use objectid-objectname'''

        return self.item.external_identifier()

    def bag_group_identifier(self):
        '''Bag group identifier: use description from MARC xml'''

        # where do we get contact phone from XML or external file?
        return self.item.bag_group_identifier()
