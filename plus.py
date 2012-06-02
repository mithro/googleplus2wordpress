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

FLAGS = gflags.FLAGS

gflags.DEFINE_string(
    'user_id', 'me', 'Google+ user id for the feed to look at')
gflags.DEFINE_boolean(
    'verbose', False, 'Should I output information I find about things.')


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
    KEY = config.EMBEDLY_KEY

    def __init__(self):
        oembed.OEmbedEndpoint.__init__(self,
            'http://api.embed.ly/1/oembed',
            ['http://*', 'https://*'])

    def request(self, *args, **kw):
        url = oembed.OEmbedEndpoint.request(self, *args, **kw)
        return '%s&key=%s' % (url, self.KEY)


# Fallback to embed.ly
OEMBED_CONSUMER.addEndpoint(Embedly())


def embed_content(url):
    """For some content we use oEmbed to get better information."""
    try:
        response = OEMBED_CONSUMER.embed(url)
        data = response.getData()

        return data
    except IOError, e:
        return False


def object_type(obj, indent=""):
    """Detect the Google plus object type.

    Object types include:
     * gallery - List of photos+videos.
     * web page - Link to a webpage.
     * photo - Post of a single photo.
     * video - Post of a single video.
     * post - Mainly text based post.
    """
    images = [att for att in obj.get('attachments', []) if att['objectType'] in ('photo', 'video')]
    articles = [att for att in obj.get('attachments', []) if att['objectType'] in ('article',)]

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
        return "post"

    print obj['content']
    print "images:", len(images), "articles:", len(articles)


def render_geocode(obj):
    """Render a HTML image of a lat/long address."""
    assert 'geocode' in obj

    coordinates = ",".join(obj['geocode'].split())
    assert len(coordinates.split(',')) == 2

    address = obj.get('address', '')
    placename = obj.get('placeName', '')
    return """
<div class="geocode">
    <a href="http://maps.google.com/?ll=%(coordinates)s&q=%(coordinates)s">
        <img src="http://maps.googleapis.com/maps/api/staticmap?center=%(coordinates)s&zoom=12&size=75x75&maptype=roadmap&markers=size:small|color:red|%(coordinates)s&sensor=false" class="alignleft">
        %(placename)s
        %(address)s
    </a>
</div>
""" % locals()


def render_object(otype, oid, obj, indent="    "):
    output = []
    if otype == "gallery":
        output.append(render_gallery(oid, obj['attachments'], indent))

    elif otype == "web page":
        output.append(render_webpage(oid, obj['attachments'], indent))

    elif otype in ("photo", "video"):
        assert len(obj['attachments']) == 1
        obj = obj['attachments']
        if otype == "photo":
            output.append(render_photo(oid, obj[0], indent))

        elif otype == "video":
            output.append(render_video(oid, obj[0], indent))

    return "".join(output)


def render_webpage(oid, obj, indent):

    webpage = None
    images = []
    for bits in obj:
        if bits['objectType'] == 'article':
            assert webpage is None
            webpage = bits
        elif bits['objectType'] in ('photo', 'video'):
            images.append(bits)

    embedly_info = OEMBED_CONSUMER.embed(webpage['url']).getData()

    if FLAGS.verbose:
        print "Google+ info"
        pprint.pprint(webpage)
        pprint.pprint(images)
        print "Embedly info"
        pprint.pprint(embedly_info)

    # FIXME: need to get this title back up somehow?
    newtitle = embedly_info

    if 'url' not in embedly_info:
        embedly_info['url'] = webpage['url']

    output = [indent, """\
<a href="%(url)s">%(description)s
""" % embedly_info]

    if 'html' in embedly_info:
        output.extend(["\n", embedly_info['html'], "\n"])
        # FIXME: Should do some type of fallback to the image version if
        # something is wrong with the HTML.

    # We prefer embedly thumbnails, unless G+ has multiple images
    elif 'thumbnail_url' in embedly_info and len(images) < 2:
        output.append(indent+"""\
  <img class="alignnone" src="%(thumbnail_url)s">
""" % embedly_info)
    elif images:
        for image in images:
            print image
            output.append(indent+"""\
  <img class="alignnone" src="%(url)s" alt="%(content)s">
""" % image['fullImage'])

    output.append(indent+"</a>")
    return "".join(output)


def render_photo(oid, obj, indent):
    #embed_info = embed_content(obj['url'])
    return """
%(indent)s<img class="alignnone" src="%(preview_url)s" alt="%(content)s">
""" % {'indent': indent,
       'preview_url': obj['image']['url'],
       'url': obj['fullImage']['url'],
       'content': obj['fullImage'].get('content', ''),
       }

def render_video(oid, obj, indent):
    """Render a video object.

    Wordpress has mostly inbuilt support for recognizing video URLs, we we just
    include a link to it on it's own line.
    """
    #embed_info = embed_content(obj['url'])
    return """

%(indent)s%(url)s

""" % {'indent': indent, 'url': obj['url']}


def render_gallery(oid, obj, indent):
    output = ["""
%(indent)s<div id="plus_gallery_%(oid)s">
""" % locals()]

    for i, nobj in enumerate(obj):
        if i == 5:
            output.append("""
%(indent)s    <div style="display: none;">
""" % locals())
            indent += "    "

        embed_info = embed_content(nobj['url'])
        if embed_info:
            embed_info['i'] = i
            embed_info['oid'] = oid
            embed_info['indent'] = indent
            embed_info['description'] = embed_info.get('description', embed_info['title'])

            if 'html' in embed_info:
                output.append("""
%(indent)s    <a href="#"
%(indent)s        id="plus_gallery_%(oid)s"
%(indent)s        onclick="return hs.expand(this, { autoplay: false, slideshowGroup: 'plus_gallery_%(oid)s' })"
%(indent)s        class="highslide">
%(indent)s        <img src="%(thumbnail_url)s"
%(indent)s            id="plus_gallery_%(oid)s_%(i)s"
%(indent)s            class="shashinThumbnailImage"
%(indent)s            alt="%(description)s"
%(indent)s            title="%(title)s"
%(indent)s            />
%(indent)s    </a>
%(indent)s    <div class="highslide-maincontent">
%(indent)s%(html)s
%(indent)s    </div>""" % embed_info)
            else:
                output.append("""
%(indent)s    <a href="%(url)s"
%(indent)s        id="plus_gallery_%(oid)s"
%(indent)s        onclick="return hs.expand(this, { autoplay: false, slideshowGroup: 'plus_gallery_%(oid)s' })"
%(indent)s        class="highslide">
%(indent)s        <img src="%(thumbnail_url)s"
%(indent)s            id="plus_gallery_%(oid)s_%(i)s"
%(indent)s            class="shashinThumbnailImage"
%(indent)s            alt="%(description)s"
%(indent)s            title="%(title)s"
%(indent)s            />
%(indent)s    </a>""" % embed_info)

        else:
            output.append("""
%(indent)s    <a href="%(original_url)s"
%(indent)s        id="plus_gallery_%(oid)s"
%(indent)s        onclick="return hs.expand(this, { autoplay: false, slideshowGroup: 'plus_gallery_%(oid)s' })"
%(indent)s        class="highslide">
%(indent)s        <img src="%(thumbnail_url)s"
%(indent)s            class="shashinThumbnailImage" id="plus_gallery_%(oid)s_%(i)s" />
%(indent)s    </a>""" % {
                'i': i,
                'oid': oid,
                'indent': indent,
                'thumbnail_url': nobj['image']['url'],
                'original_url': nobj.get('fullImage', nobj['embed'])['url'],
                })


    if i >= 5:
        indent = indent[:-4]
        output.append("""
%(indent)s    </div>
""" % locals())

    output.append("""
%(indent)s</div>
%(indent)s<script type="text/javascript">addHSSlideshow('plus_gallery_%(oid)s');</script>""" % locals())

    return "".join(output)

"""
                        'meta_query' => array(
                                array(
                                        'key' => 'google_plus_activity_id',
                                        'value' => $item->id,
                                ),
"""


def main(argv):
  # Let the gflags module process the command-line arguments
  try:
    argv = FLAGS(argv)
  except gflags.FlagsError, e:
    print '%s\\nUsage: %s ARGS\\n%s' % (e, argv[0], FLAGS)
    sys.exit(1)

  # If the Credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # Credentials will get written back to a file.
  storage = Storage('plus.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(FLOW, storage)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  service = build("plus", "v1", http=http)

  try:
    person = service.people().get(userId=FLAGS.user_id).execute(http)

    request = service.activities().list(
        userId=person['id'], collection='public')

    print "\n"*10
    while ( request != None ):
      activities_doc = request.execute()
      for item in sorted(activities_doc.get('items', []), key=lambda x: x["id"]):

        print "="*80
        print 'ID: %-040s' % item['id']

        # Convert content to HTML so we can:
        #  * Determine if the page has content
        #  * Create a better title
        H2T = html2text.HTML2Text()
        H2T.ignore_links = True
        H2T.ignore_images = True
        H2T.ignore_emphasis = True
        H2T.body_width = 0
        txtcontent = H2T.handle(item['object']['content'])
        lines = [x for x in txtcontent.split('\n') if x.strip()]
        if not lines:
            title = ''
            has_content = False
        else:
            # Take the first sentence as the title
            tokenizer = nltk.PunktSentenceTokenizer()
            sentences = tokenizer.tokenize(lines[0])
            title = sentences[0].strip()

            # If we just have a link, guess we don't have a title
            if title.startswith('http://') or title.startswith('https://'):
                title = ''

            has_content = bool(sentences[1:]) or bool(lines[1:])

        otype = object_type(item['object'])
        print repr((title, has_content, otype))

        # If item['object'] has an id then it's a reshare,
        if item['object'].get('id', ''):
            author = item['object']['actor']['displayName']
            title = '%sReshared %s from %s' % (['', "%s - " % title][len(title) > 1], otype, author)

            content = item['annotation']

        # else, original post
        else:
            print "-"*80
            print render_object(otype, item['id'], item['object'])
            print "-"*80

      request = service.activities().list_next(request, activities_doc)

  except AccessTokenRefreshError:
    print ("The credentials have been revoked or expired, please re-run"
      "the application to re-authorize")

if __name__ == '__main__':
  main(sys.argv)


