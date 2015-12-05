DKB Downloader
=====================
The German bank DKB makes bank statements for their credit cards and checking accounts available as PDF files on their banking web site.

DKB Downloader will log in to the web site and download all PDFs in the "Briefkasten" that are not already downloaded and present in the 
configured download directory.

DKB Downloader is based on `"DKB VISA QIF Exporter" by Christian Hoffmann <https://github.com/hoffie/dkb-visa>`. It borrows all the codes 
to access the DKB web site from the project. 


Requirements
------------
You need Python 2.7.x, BeautifulSoup and mechanize. On current Ubuntu,
this should suffice:

    apt-get install python-bs4 python-mechanize

Usage
-----
    ./dkbdownloader.py --userid USER

with USER being the name you are using at the regular DKB online banking web site as well.
You will be asked for your PIN and the bank downloaded documents should be stored under /my/download/directory/<userid>/.

If this script is of any help for you, please let me know. :)
