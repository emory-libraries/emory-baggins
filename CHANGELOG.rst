CHANGELOG
=========

Release 0.9
-----------

* As a bagger, I want a record of when and why a valid Bag is not successfully generated,  so that I can investigate and correct the problem.
* As a bagger of LSDI books, I want information about how the payload files relate to each other, so that bag contents can be re-assembled into a digital book object for ingest into a digital repository
* As a bagger, I want to generate an External Description so I or other organizations can easily see what the content of the bag is.
* Baggins: update to new bagit-python master and revert to previous directory structure -- address Rebecca's issue #68
* FedoraAdmin access for 'jfenton'
* Incorrect mime type in METS for .pos files
* Handling diacritics in MARC records
* As a bagger of LSDI books, I want all relevant technical metadata about the payload to be recorded, to aid digital preservation of the payload
* As a bagger of LSDI books, I want a human readable summary of which external relationships are recorded for the material, so that others can more easily interpret the machine readable version of the metadata.
* As a bagger of LSDI books, I want a human readable summary of what type of audits/activity logs are available for the material, so that I am informed about its preservation history.
* As a bagger of LSDI books, I want a human readable summary of what type of identifiers are provided for the material, so that others can more easily interpret the machine readable version of the metadata.
* As a bagger of LSDI books, I want to provide a human readable summary of all relevant rights information in the bag, so that I know later how I can legally make use of the content of the bag
* As a bagger of LSDI books, I want a human readable summary of what types of descriptive metadata is available for the material, so that others can interpret the enclosed metadata files.
* As a bagger of LSDI books, I want all necessary server connections and file access to be verified before bag construction, so that partial invalid bags are less likely to be created when running the script

Release 0.5
-----------


* As a bagger, I want to run a script based on one or more individual IDs
  from the DigWF database, so that I can target selected content to Bag.
* As a bagger, I want to be able to install a script using provided
  instructions, so that I don't require personal technical support at the
  time of installation.
* As a bagger, I want to select a location for the output for the bags
  so that I can specify where the bags should be stored.
* As a bagger, I need to configure environments and source files, so
  that I can access the correct servers and data sources.
* As a bagger, I want to run a script based on a supplied file containing
  many IDs, so that I can target selected content to bag.
* As a bagger of LSDI books, I want all .tif, .pos, .txt, .pdf, and .xml
  (ABBYY Finereader) files to be added to the bag payload, so that all data
  comprising a digitized book is included in the bag.
* As a bagger, I want to record the bagit version and character encoding used
  when creating the bag, so that my bags conform to the bagit specification.
* As a bagger, I want md5 and sha256 checksums to be generated for all payload
  (data) and metadata files in the bag, so that file fixity can be preserved.
* As a bagger of LSDI books, I want MARCXML records for the digitized volume to
  be added to the bag, so that sufficient descriptive metadata is included.
* As a bagger, I want to record summary information about the source
  organization contained in the bag, so that we know who owns the content.
* As a bagger of LSDI books, I want to record notes about external relationships
  regarding collection membership and related book object in Fedora, so that
  those relationships are clear and explicit inside the bag.

