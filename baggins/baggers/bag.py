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

    def copy_data_files(self, bagdir):
        '''Copy data files into the bag staging directory.'''
        for datafile in self.data_files():
            # use copy2 to preserve original file statistics
            shutil.copy2(datafile, bagdir)
            datafile_base = os.path.basename(datafile)
            # make sure file is writable so bagit can move it,
            # otherwise bagit will error
            # NOTE: depending on file ownership, this may not be the
            # permissions we actually need...
            os.chmod(os.path.join(bagdir, datafile_base), 0644)

    def create_bag(self, basedir):
        '''Create a bagit bag for this item.'''
        bagdir = os.path.join(basedir, self.bag_name())
        os.mkdir(bagdir)

        # add data to the bag
        self.copy_data_files(bagdir)

        bag = bagit.make_bag(bagdir, checksum=self.checksum_algorithms)
        return bag
