#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# DKB Bank statement downloader
# Copyright (C) 2015 Ralph Borchers <dkbdownloader@ebrn.de>
#
# Based on
# Copyright (C) 2013 Christian Hoffmann <mail@hoffmann-christian.info>
#
# Inspired by Jens Herrmann <jens.herrmann@qoli.de>,
# but written using modern tools (argparse, csv reader, mechanize,
# BeautifulSoup)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import csv
import sys
import os
import logging
import mechanize
from mechanize._response import closeable_response, response_seek_wrapper
from StringIO import StringIO
import bs4

DEBUG = False


logger = logging.getLogger(__name__)
downloadDir = "/my/download/directory"

def get_bs(data):
    """
    get_bs returns a new BeautifulSoup instance with the best
    available parser. We have our own creation logic in order to avoid
    unnecessary warnings or creating new dependencies.
    """
    for parser in ("lxml", "html.parser", None):
        try:
            bs = bs4.BeautifulSoup(data, parser)
            logger.debug("choosing beatifulsoup parser %s", parser)
            return bs
        except bs4.FeatureNotFound:
            continue
    logger.error("unable to create a working beautifulsoup instance")


class DKBBrowser(mechanize.Browser):
    """
    DKBBrowser is a mechanize.Browser which automatically fixes an HTML
    coding problem in the dkb.de non-js website.
    Sadly, this code must access non-public interfaces of mechanize.
    Let's hope, this code is only temporarily necessary...
    """
    def open(self, *args, **kwargs):
        response = mechanize.Browser.open(self, *args, **kwargs)
        if not response or not response.get_data():
            return response
        html = response.get_data().replace("<![endif]-->",
            "<!--[endif]-->")
        patched_resp = closeable_response(StringIO(html), response._headers,
            response._url, response.code, response.msg)
        patched_resp = response_seek_wrapper(patched_resp)
        self.set_response(patched_resp)
        return patched_resp

class DkbScraper(object):
    BASEURL = "https://banking.dkb.de/dkb/-"

    def __init__(self):
        self.br = DKBBrowser()

    def login(self, userid, pin):
        """
        Create a new session by submitting the login form
        @param str userid
        @param str pin
        """
        logger.info("Starting login as user %s...", userid)
        br = self.br

        # we are not a spider, so let's ignore robots.txt...
        br.set_handle_robots(False)

        # Although we have to handle a meta refresh, we disable it here
        # since mechanize seems to be buggy and will be stuck in a
        # long (infinite?) sleep() call
        br.set_handle_refresh(False)

        br.open(self.BASEURL + '?$javascript=disabled')

        # select login form:
        br.form = list(br.forms())[0]

        br.set_all_readonly(False)
        br.form["j_username"] = userid
        br.form["j_password"] = pin
        br.form["browserName"] = "Firefox"
        br.form["browserVersion"] = "40"
        br.form["screenWidth"] = "1000"
        br.form["screenHeight"] = "800"
        br.form["osName"] = "Windows"
        br.submit()
        br.open(self.BASEURL + "?$javascript=disabled")

    def navigate_to_postbox_overview(self):
        """
        Navigates the internal browser state to the postbox
        overview
        """
        logger.info("Navigating to 'Briefkasten'...")
        br = self.br
        overview_html = get_bs(br.response().read())
        for link in br.links():
            if re.search("Briefkasten", link.text, re.I):
                br.follow_link(link)
                return
            if 'weitergeleitet' in link.text:
                br.follow_link(link)
            if link.text == 'here':
                br.follow_link(text="here")
        raise RuntimeError("Unable to find link 'Briefkasten' -- "
            "Maybe the login went wrong?")
        
    def download_docs(self):
        """
        find all links pointing to a document download
        and download the docs 
        """
        logger.info("Finding Download links")
        br=self.br
        overview_html = get_bs(br.response().read())
        for link in br.links():
            if re.search("download=true",link.url,re.I):
                #print link
                filenameMatch = re.search('.*filename=(.*)&download=true',link.url)
                if filenameMatch:
                    downloadDestination = os.path.join(downloadDir,args.userid,filenameMatch.group(1) + ".pdf")
                    if not os.path.isfile(downloadDestination):
                        print ("Downloading Document " + filenameMatch.group(1))
                        if DEBUG: print link
                        br.retrieve("https://banking.dkb.de" + link.url, downloadDestination)
                    else:
                        print ("File exists - Not Downloading " + filenameMatch.group(1))

      
    def navigate_to_tax_info_overview(self):
        """
        Navigates the internal browser state to the tax info
        overview
        """
        logger.info("Navigating to 'Steuerinformationen'...")
        br = self.br
        overview_html = get_bs(br.response().read())
        for link in br.links():
            if re.search("Steuerinformationen", link.text, re.I):
                br.follow_link(link)
                return
            if 'weitergeleitet' in link.text:
                br.follow_link(link)
            if link.text == 'here':
                br.follow_link(text="here")
        raise RuntimeError("Unable to find link 'Steuerinformationen' -- "
            "Maybe the login went wrong?")
    
if __name__ == '__main__':
    from getpass import getpass
    from argparse import ArgumentParser
    from datetime import date

    level = logging.INFO
    if DEBUG:
        level = logging.DEBUG
    logging.basicConfig(level=level, format='%(message)s')

    cli = ArgumentParser()
    cli.add_argument("--userid",
        help="Your user id (same as used for login)")
    
    args = cli.parse_args()
    if not args.userid:
        cli.error("Please specify a valid user id") 
    
    
    pin = ""
    import os
    if os.isatty(0):
        while not pin.strip():
            pin = getpass('PIN: ')
    else:
        pin = sys.stdin.read().strip()

    fetcher = DkbScraper()

    if DEBUG:
        logger = logging.getLogger("mechanize")
        logger.addHandler(logging.StreamHandler(sys.stdout))
        logger.setLevel(logging.INFO)
        #fetcher.br.set_debug_http(True)
        fetcher.br.set_debug_responses(True)
        #fetcher.br.set_debug_redirects(True)

    fetcher.login(args.userid, pin)
    fetcher.navigate_to_postbox_overview()
    fetcher.download_docs()
    fetcher.navigate_to_tax_info_overview()
    fetcher.download_docs()
    
