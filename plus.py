#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:
#
# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Program to export your Google+ stream to a Wordpress Blog.

Command-line application that retrieves the users latest content and
then adds a new entry.

Usage:
  $ python plus.py

You can also get help on all the command-line flags the program understands
by running:

  $ python plus.py --help
"""

__author__ = "tansell@google.com (Tim 'mithro' Ansell)"

import config

import gflags
import httplib2
import logging
import os
import pprint
import sys
import re

import oembed
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run

import html2text
import nltk
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts

FLAGS = gflags.FLAGS

gflags.DEFINE_string(
    'user_id', 'me', 'Google+ user id for the feed to look at')
gflags.DEFINE_boolean(
    'verbose', False, 'Should I output information I find about things.')


# Code to deal with Google+'s OAuth stuff
###############################################################################
CLIENT_SECRETS = 'client_secrets.json'
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/plus.me',
    message=MISSING_CLIENT_SECRETS_MESSAGE)


# Code to get more information about posted contents using oembed protocol
###############################################################################


OEMBED_CONSUMER = oembed.OEmbedConsumer()
# My customer PicasaWeb/Google+ OEmbed endpoint
OEMBED_CONSUMER.addEndpoint(
    oembed.OEmbedEndpoint(
        'http://picasaweb-oembed.appspot.com/oembed',
        ['http://picasaweb.google.com/*',
             'https://picasaweb.google.com/*',
             'http://plus.google.com/photos/*',
             'https://plus.google.com/photos/*'])
    )


class Embedly(oembed.OEmbedEndpoint):
    KEY = False

    def __init__(self, key):
        oembed.OEmbedEndpoint.__init__(self,
            'http://api.embed.ly/1/oembed',
            ['http://*', 'https://*'])
        self.KEY = key

    def request(self, *args, **kw):
        url = oembed.OEmbedEndpoint.request(self, *args, **kw)
        return '%s&key=%s' % (url, self.KEY)


# Fallback to embed.ly
OEMBED_CONSUMER.addEndpoint(Embedly(config.EMBEDLEY_KEY))


def embed_content(url):
    """For some content we use oEmbed to get better information."""
    try:
        response = OEMBED_CONSUMER.embed(url)
        data = response.getData()

        return data
    except IOError, e:
        return False


# Code to render templates
###############################################################################
from jinja2 import Environment, FileSystemLoader
env = Environment(
    loader=FileSystemLoader('templates'),
    comment_start_string='{% comment %}',
    comment_end_string='{% endcomment %}',
    )


def render_tmpl(filename, content):
    if 'self' in content:
        del content['self']
    template = env.get_template(filename)
    return template.render(**content)


# Google Plus post types
###############################################################################

class GooglePlusPost(object):
    TYPE = None

    TYPE2CLASS = {}

    @staticmethod
    def type(gdata):
        """Detect the Google plus object type.

        Object types include:
         * gallery - List of photos+videos.
         * web page - Link to a webpage.
         * photo - Post of a single photo.
         * video - Post of a single video.
         * post - Mainly text based post.
        """
        images = [
            att for att in gdata.get('attachments', [])
            if att['objectType'] in ('photo', 'video')]
        articles = [
            att for att in gdata.get('attachments', [])
            if att['objectType'] in ('article',)]

        # If the post has multiple images/videos we produce a gallery post
        if len(images) > 1:
            return "gallery"

        # If the post has an article, then we render an article post
        elif articles:
            return "web page"

        # If the post has a single image, then we render an image post
        elif images:
            return images[0]['objectType']

        # Otherwise, it's a standard blog post
        else:
            return "text"

    def __init__(self, gid, gdata, gcomment):
        assert self.TYPE

        self.gid = gid
        self.gdata = gdata
        self.gcomment = gcomment

        self.tags = []
        self.media = []
        self.comments = []

        self.content = None
        self.title = None

        # Convert content to HTML so we can:
        #  * Determine if the page has content
        #  * Create a better title
        H2T = html2text.HTML2Text()
        H2T.ignore_links = True
        H2T.ignore_images = True
        H2T.ignore_emphasis = True
        H2T.body_width = 0
        txtcontent = H2T.handle(self.gdata['object']['content'])
        lines = [x for x in txtcontent.split('\n') if x.strip()]
        if not lines:
            self.has_content = False
            self.title = None
        else:
            # Take the first sentence as the title
            tokenizer = nltk.PunktSentenceTokenizer()
            sentences = tokenizer.tokenize(lines[0])
            self.title = sentences[0].strip()

            # If we just have a link, guess we don't have a title
            if self.title.startswith('http://') \
                    or self.title.startswith('https://'):
                self.title = None

            self.has_content = bool(sentences[1:]) or bool(lines[1:])

            # FIXME: Should we strip the title from the content?
            self.content = self.gdata['object']['content']

    # TODO: Actually use this
    def render_geocode(self):
        """Render a HTML image of a lat/long address."""
        if 'geocode' not in self.gdata:
            return False

        coordinates = ",".join(self.gdata['geocode'].split())
        assert len(coordinates.split(',')) == 2

        address = self.gdata.get('address', '')
        placename = self.gdata.get('placeName', '')
        return self.render_tmpl('geocode.html', locals())

    def toWordPressPost(self):
        post = WordPressPost()

        if self.title:
            post.title = self.title

        if self.content:
            post.content = self.content

        post.post_status = 'publish'
        return post


class GalleryPost(GooglePlusPost):
    TYPE = 'gallery'

    def render(self):
        obj = self.gdata['object']['attachments']

        tmpl_data = []
        for nobj in obj:
            embed_info = embed_content(nobj['url'])
            if embed_info:
                embed_info['description'] = embed_info.get(
                    'description', embed_info['title'])
                embed_info['src'] = 'embedly'

                tmpl_data.append(embed_info)
            else:
                tmpl_data.append({
                    'src': 'g+',
                    'thumbnail_url': nobj['image']['url'],
                    'original_url': nobj.get('fullImage', nobj.get(
                        'embed', {'url': '***FIXME***'}))['url'],
                    })

        self.content = render_tmpl('gallery.html', {
            'gid': self.gid,
            'attachments': tmpl_data,
            })


GooglePlusPost.TYPE2CLASS['gallery'] = GalleryPost


class WebPagePost(GooglePlusPost):
    TYPE = 'web page'

    def render(self):
        obj = self.gdata['object']['attachments']

        webpage = None
        images = []
        for bits in obj:
            if bits['objectType'] == 'article':
                assert webpage is None
                webpage = bits
            elif bits['objectType'] in ('photo', 'video'):
                images.append(bits)

        edata = embed_content(webpage['url'])
        if not self.title and edata['title']:
            self.title = edata['title']

        has_edata_html = 'html' in edata
        has_edata_image = 'thumbnail_url' in edata
        has_images = len(images) > 2
        has_preview = has_edata_html or has_edata_image or has_images

        self.content = render_tmpl('webpage.html', locals())


GooglePlusPost.TYPE2CLASS['web page'] = WebPagePost


class PhotoPost(GooglePlusPost):
    TYPE = 'photo'

    def render(self):
        obj = self.gdata['object']['attachments'][0]
        self.content = """
<img class="alignnone" src="%(preview_url)s" alt="%(content)s">
""" % {'preview_url': obj['image']['url'],
       'url': obj['fullImage']['url'],
       'content': obj['fullImage'].get('content', ''),
       }


GooglePlusPost.TYPE2CLASS['photo'] = PhotoPost


class VideoPost(GooglePlusPost):
    TYPE = 'video'

    def render(self):
        obj = self.gdata['object']['attachments'][0]
        self.content = """%(url)s""" % {'url': obj['url']}


GooglePlusPost.TYPE2CLASS['video'] = VideoPost


class TextPost(GooglePlusPost):
    TYPE = 'text'

    def render(self):
        pass

GooglePlusPost.TYPE2CLASS['text'] = TextPost

###############################################################################


def main(argv):
    # Let the gflags module process the command-line arguments
    try:
        argv = FLAGS(argv)
    except gflags.FlagsError, e:
        print '%s\\nUsage: %s ARGS\\n%s' % (e, argv[0], FLAGS)
        sys.exit(1)

    # If the Credentials don't exist or are invalid run through the native
    # client flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage('plus.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage)

    # Create an httplib2.Http object to handle our HTTP requests and authorize
    # it with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    service = build("plus", "v1", http=http)
    wp = Client(
         config.WORDPRESS_XMLRPC_URI,
         config.WORDPRESS_USERNAME,
         config.WORDPRESS_PASSWORD
    )

    try:
        person = service.people().get(userId=FLAGS.user_id).execute(http)

        request = service.activities().list(
            userId=person['id'], collection='public')

        i = 0
        n = 100
        existing_posts = more_posts = []
        while True:
            i = n + i
            more_posts = wp.call(posts.GetPosts({"number": n, 'offset': i}))
            existing_posts += more_posts

            if len(more_posts) == 0:
                break

        while request is not None:
            activities_doc = request.execute()

            items = sorted(
                activities_doc.get('items', []),
                key=lambda x: x["id"]
            )

            for item in items:
                if FLAGS.verbose:
                    print 'Assessing / Publishing ID: %-040s' % item['id']

                otype = GooglePlusPost.type(item['object'])

                # If item['object'] has an id then it's a reshare,
                if item['object'].get('id', ''):
                    author = item['object']['actor']['displayName']
                    post = TextPost()
                    post.title = '%sReshared %s from %s' % (
                        ['', "%s - " % post.title][len(post.title) > 1],
                        otype, author)
                    post.content = item['annotation']
                    if FLAGS.verbose:
                        print repr(('Reshare!', post.title, post.content))

                # else, original post
                else:
                    post = GooglePlusPost.TYPE2CLASS[otype](
                        item['id'], item, [])
                    if FLAGS.verbose:
                        print repr((post.title, post.has_content, otype))
                        print "=" * 80
                        post.render()
                        print post.content
                        print "-" * 80

                found = False
                for existing_post in existing_posts:
                    for field in existing_post.custom_fields:
                        if field['key'] == 'google_plus_activity_id' \
                            and field['value'] == item['id']:
                            found = existing_post

                publishable_post = post.toWordPressPost()
                # TODO Do we actually support anything which isn't an activity?
                # TODO Surely a GooglePost object could know its own ID
                publishable_post.custom_fields = [
                    {"key": 'google_plus_activity_id', "value": item['id']}
                ]

                #post.author = author
                if not post.title:
                    if FLAGS.verbose:
                        print "Cannot find title!"

                if not post.content:
                    if FLAGS.verbose:
                        print "Cannot find content!"

                if post.title and post.content and not found:
                    if FLAGS.verbose:
                        print "Publishing new post"
                    wp.call(posts.NewPost(publishable_post))

                # Todo check equality, no point editing if nothing changes
                if post.title and post.content and found:
                    if found.content != post.content \
                        or found.title != post.title:
                        if FLAGS.verbose:
                            print "Updating existing post"
                        wp.call(posts.EditPost(found.id, publishable_post))

                request = service.activities().list_next(
                              request, activities_doc
                          )
            break

    except AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
                 "the application to re-authorize")

if __name__ == '__main__':
    main(sys.argv)
