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
import base64
from datetime import date, time
import mimetypes

import gflags
import httplib2
import urllib2
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
from wordpress_xmlrpc import WordPressComment, AnonymousMethod
from wordpress_xmlrpc.methods import posts, comments, media
from wordpress_xmlrpc.compat import xmlrpc_client
import wordpress_xmlrpc
import xmlrpclib

from dateutil.parser import parse as date_parse

FLAGS = gflags.FLAGS

gflags.DEFINE_string(
    'user_id', 'me', 'Google+ user id for the feed to look at')
gflags.DEFINE_boolean(
    'verbose', False, 'Should I output information I find about things.')
gflags.DEFINE_boolean(
    'dryrun', False, "Don't upload anything to wordpress yet.")
gflags.DEFINE_string(
    'post_id', None, 'Google+ post id for the tool to look at.')


# Fix wordpress_xmlrpc's __repr__ function to use unicode(self) instead of
# str(self)
def WordPressBase__repr__(self):
    return '<%s: %s>' % (
        self.__class__.__name__, unicode(self).encode('utf-8'))
wordpress_xmlrpc.WordPressBase.__repr__ = WordPressBase__repr__


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
        oembed.OEmbedEndpoint.__init__(
            self,
            'http://api.embed.ly/1/oembed',
            ['http://*', 'https://*']
        )

        self.KEY = key

    def request(self, *args, **kw):
        url = oembed.OEmbedEndpoint.request(self, *args, **kw)
        return '%s&key=%s' % (url, self.KEY)

# Fallback to embed.ly
OEMBED_CONSUMER.addEndpoint(Embedly(config.EMBEDLY_KEY))


def embed_content(url):
    """For some content we use oEmbed to get better information."""
    try:
        response = OEMBED_CONSUMER.embed(url)
        data = response.getData()

        return data
    except IOError, e:
        print e
        return False

def upload_wordpress_photo(url, name):
    """ For image in googleplus, download it and upload it to wordpress """
    #download image from url.
    try:
        content = urllib2.urlopen(url).read()
    except:
        print("Could not download %(url)s", url)
        return ""

    data = {}
    data['name'] = name
    data['type'] = mimetypes.guess_type(url) or mimetypes.guess_type(url)[0]
    data['bits'] = xmlrpc_client.Binary(content)
    result = wp.call(media.UploadFile(data))
    return result


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


# See https://github.com/maxcutler/python-wordpress-xmlrpc/pull/35
class NewAnonymousComment(AnonymousMethod):
    """
    Create a new comment on a post without authenticating.

    Parameters:
        `post_id`: The id of the post to add a comment to.
        `comment`: A :class:`WordPressComment` instance with
                   at least the `content` value set.

    Returns: ID of the newly-created comment (an integer).
    """
    method_name = 'wp.newComment'
    method_args = ('post_id', 'comment')


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
        albums = [
            att for att in gdata.get('attachments', [])
            if att['objectType'] in ('album',)
        ]

        # If the post has multiple images/videos we produce a gallery post
        if len(images) > 1 or albums:
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

    def __init__(self, gid, gdata):
        assert self.TYPE

        self.gid = gid
        self.gdata = gdata

        self.tags = []
        self.media = []
        self.comments = []

        self.content = None
        self.title = None

        self.published = date_parse(self.gdata['published'])
        self.updated = date_parse(self.gdata['updated'])

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
        return render_tmpl('geocode.html', locals())

    def toWordPressPost(self):
        post = WordPressPost()

        if self.title:
            post.title = self.title

        if self.content:
            post.content = self.content

        post.date = self.published
        post.date_modified = self.updated
        post.comment_status = True

        post.post_status = 'publish'
        return post


class GalleryPost(GooglePlusPost):
    TYPE = 'gallery'

    def render(self):
        obj = self.gdata['object']['attachments']
        #in case of the gallery. All pictures will be in obj[0]['thumbnails']
        if len(obj) <= 1:
            obj = obj[0]['thumbnails']
        tmpl_data = []
        for nobj in obj:
            #new_url = upload_wordpress_photo(nobj['url'], nobj['name'])
            embed_info = embed_content(nobj['url'])
            if embed_info:
                embed_info['description'] = embed_info.get(
                    'description', embed_info['title'])
                embed_info['src'] = 'embedly'
                embed_info['url'] = upload_wordpress_photo(embed_info['url'], embed_info['title'])['url']
                embed_info['thumbnail_url'] = upload_wordpress_photo(embed_info['thumbnail_url'], embed_info['title'])['url']

                tmpl_data.append(embed_info)
            else:
                tmpl_data.append({
                    'src': 'g+',
                    'thumbnail_url': upload_wordpress_photo(nobj['image']['url'], nobj['title'])['url'],
                    'original_url': nobj.get('fullImage', nobj.get(
                        'embed', {'url': '***FIXME***'}))['url'],
                })

        self.content = render_tmpl('gallery.html', {
            'gid': self.gid,
            'attachments': tmpl_data,
        })
        self.content += self.gdata['object']['content']


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
        if FLAGS.verbose:
            print "Embedly data for '%s'" % webpage['url']
            pprint.pprint(edata)

        if edata:
            if not self.title and edata['title']:
                self.title = edata['title']

            has_edata_html = 'html' in edata
            has_edata_image = 'thumbnail_url' in edata
        else:
            has_edata_html = False
            has_edata_image = False

        has_images = len(images) > 2
        has_preview = has_edata_html or has_edata_image or has_images

        self.content = render_tmpl('webpage.html', locals()) + self.gdata['object']['content']


GooglePlusPost.TYPE2CLASS['web page'] = WebPagePost


class PhotoPost(GooglePlusPost):
    TYPE = 'photo'

    def render(self):
        main_content = self.gdata['object']['content']
        obj = self.gdata['object']['attachments'][0]

        try:

            preview_url = obj['image']['url']
            full_url = obj['fullImage']['url']
            content = obj['fullImage'].get('content', '')
        except KeyError:
            edata = embed_content(obj['url'])
            if FLAGS.verbose:
                print "Embedly data for '%s'" % obj['url']
                pprint.pprint(edata)
            assert edata, "No Embedly data for %s" % obj['url']

            if not self.title and edata.get('title', None):
                self.title = edata['title']

            preview_url = upload_wordpress_photo(edata.get('thumbnail_url', obj['url']), edata.get('name'))['url']
            full_url = upload_wordpress_photo(obj['url'], edata.get('name'))['url']
            content = edata.get('description', '')

        self.content = """
<img class="alignnone" src="%(preview_url)s" alt="%(content)s">
%(main_content)s
""" % locals()


GooglePlusPost.TYPE2CLASS['photo'] = PhotoPost


class VideoPost(GooglePlusPost):
    TYPE = 'video'

    def render(self):
        main_content = self.gdata['object']['content']
        obj = self.gdata['object']['attachments'][0]
        self.content = """
<iframe width="420" height="345" src="%(url)s"> </iframe> <br /> %(main_content)s
""" % {'url': obj['url'].strip(), 'main_content': main_content}


GooglePlusPost.TYPE2CLASS['video'] = VideoPost


class TextPost(GooglePlusPost):
    TYPE = 'text'

    def render(self):
        self.content = self.gdata['object']['content']
        pass

GooglePlusPost.TYPE2CLASS['text'] = TextPost


class GooglePlusComment(object):

    def __init__(self, gdata):
        self.id = gdata['id']
        self.content = gdata['object']['content']
        self.author_name = gdata['actor']['displayName']
        self.author_id = gdata['actor']['id']
        self.author_url = gdata['actor']['url']
        self.author_image = gdata['actor']['image']['url']
        self.custom_fields = {'key':'google_plus_comment_avatar', 'value':gdata['actor']['image']['url']}

    # TODO Comment author must fill out name and
    #      e-mail setting is currently unchecked
    # TODO Author details are ignored!
    def toWordPressComment(self):
        comment = WordPressComment()

        comment.content = self.content
        comment.author = self.author_name
        comment.author_url = self.author_url
        comment.author_image = self.author_image
        comment.custom_fields = self.custom_fields
        return comment

###############################################################################
if not FLAGS.dryrun:
    wp = Client(
        config.WORDPRESS_XMLRPC_URI,
        config.WORDPRESS_USERNAME,
        config.WORDPRESS_PASSWORD
    )

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

    try:
        #get G+ people information
        person = service.people().get(userId=FLAGS.user_id).execute(http)

        #get posted of a person.
        post_request = service.activities().list(
            userId=person['id'], collection='public')

        i = 0
        n = 100
        #get all post in wordpress
        existing_posts = more_posts = []
        while True and not FLAGS.dryrun:
            more_posts = wp.call(posts.GetPosts({"number": n, 'offset': i}))
            if FLAGS.verbose:
                print "Found ", i, n, more_posts

            i = n + i
            existing_posts += more_posts

            if len(more_posts) == 0:
                break

        while post_request is not None:
            activities_doc = post_request.execute()
            items = sorted(
                activities_doc.get('items', []),
                key=lambda x: x["id"]
            )

            for item in items:
                #ignore posts with posted id is not equal input post_id
                if FLAGS.post_id and FLAGS.post_id != item['id']:
                    continue

                if FLAGS.verbose:
                    print 'Assessing / Publishing ID: %-040s' % item['id']

                otype = GooglePlusPost.type(item['object'])

                # If item['object'] has an id then it's a reshare,
                if item['object'].get('id', ''):
                    author = item['object']['actor']['displayName']
                    post = TextPost(item['id'], item)
                    post.title = '%sReshared %s from %s' % (
                        ['', "%s - " % post.title][len(post.title) > 1],
                        otype, author)

                    if 'annotation' in item:
                        post.content = item['annotation']
                    if FLAGS.verbose:
                        print repr(('Reshare!', post.title, post.content))

                # else, original post
                else:
                    post = GooglePlusPost.TYPE2CLASS[otype](
                        item['id'], item)
                    if FLAGS.verbose:
                        print repr((post.title, post.has_content, otype))
                        print "=" * 80
                        post.render()
                        print post.content
                        print "-" * 80

                found = False
                for existing_post in existing_posts:
                    for field in existing_post.custom_fields:
                        field_key = field['key'] == 'google_plus_activity_id'
                        field_value = field['value'] == item['id']

                        if field_key and field_value:
                            found = existing_post
                            post_id = found.id

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

                if FLAGS.dryrun:
                    continue

                if post.title and post.content and not found:
                    if FLAGS.verbose:
                        print "Publishing new post",
                        print repr(publishable_post).decode('utf-8')
                    post_id = wp.call(posts.NewPost(publishable_post))

                # Todo check equality, no point editing if nothing changes
                if post.title and post.content and found:
                    content_match = found.content == post.content
                    title_match = found.title == post.title
                    if not (content_match and title_match):
                        if FLAGS.verbose:
                            print "Updating existing post"
                        wp.call(posts.EditPost(found.id, publishable_post))


                # Comments
                if item['object']['replies']['totalItems'] > 0 and found:
                    comments_request = service.comments().list(
                        maxResults=100,
                        activityId=item['id']
                    )
                    comments_document = comments_request.execute()

                    for comment in comments_document['items']:
                        publishable_comment = GooglePlusComment(
                            comment).toWordPressComment()

                        # TODO Check post for existing comments nad avoid
                        # duplication

                        post_id = found.id
                        if FLAGS.verbose:
                            print "Publishing new comment to " + post_id
                            #wp.call(NewAnonymousComment(post_id, publishable_comment))

# See
# https://github.com/maxcutler/python-wordpress-xmlrpc/pull/35
                        if config.WORDPRESS_COMMENT_STYLE == 'anonymous':
                            wp.call(comments.NewAnonymousComment(
                                found.id, publishable_comment))
                        else:
                            wp.call(comments.NewComment(
                                found.id, publishable_comment))

                post_request = service.activities().list_next(
                    post_request, activities_doc
                )
            break

    except AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
               "the application to re-authorize")

if __name__ == '__main__':
    main(sys.argv)
