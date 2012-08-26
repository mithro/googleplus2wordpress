#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
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

"""Test module for plus.py,

You can run the test by running:
    $ python -m tests
"""

__author__ = 'bayuadji@gmail.com'

import json
import os
import unittest

from mock import patch, MagicMock, Mock


class TestGooglePost(unittest.TestCase):
    def setUp(self):
        self.oauth2client_mock = MagicMock()
        self.oauth2client_mock.flow_from_clientsecrets = Mock()
        modules = {
            'oauth2client.client': self.oauth2client_mock,
            'oauth2client.flow_from_clientsecrets':
              self.oauth2client_mock.flow_from_clientsecrets
        }

        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()

    def tearDown(self):
        self.module_patcher.stop()

    def load_data(self, filename):
        """
        Load the file data, from json into gdata.
        """
        file_ = open(os.path.join(
            os.path.dirname(__file__),
            "test_documents", filename))

        content = file_.read()
        file_.close()
        return json.loads(content)

    def do_test_equal(self, post_class, filename, result, method=None):
        """Helper for test equal"""
        gdata = self.load_data(filename)
        gid = ''
        gcomment = {}
        post = post_class(gid, gdata, gcomment)
        post.render()
        if not method:
            self.assertEqual(result,
                         post.content.strip())
        else:
            result_tmpl = getattr(post, method, "ERROR")()
            self.assertEqual(result,
                             result_tmpl)


class TestPhoto(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost

        #we need to strip, since the render add
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh3.googleusercontent.com%2F-pO-hpo7EM7E%2FTv55RUxDaUI%2FAAAAAAAAAMk%2FW3HP0NZUdjg%2Fw288-h288%2Fcrop.png" alt="">"""
        self.do_test_equal(PhotoPost, 'pic_with_content.json', result)

    def test_photo_from_picasa_web(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh6.googleusercontent.com%2F-D0vjgEuIKFM%2FT-rhhY-iBbI%2FAAAAAAAAIJw%2FSUL6I7p1Sh4%2Fw288-h288%2FSkyline%252BWinterfest.jpg" alt="">"""
        self.do_test_equal(PhotoPost, 'sample_picasa.json', result)

    def test_photo_from_flickr(self):
        from plus import PhotoPost
        result = ''
        self.do_test_equal(PhotoPost, 'pic_flickr_without_content.json', result)

    def test_photo_from_smugmug(self):
        from plus import PhotoPost
        result = ''
        self.do_test_equal(PhotoPost, 'sample_smugmug.json', result)


class TestVideo(TestGooglePost):
    def test_video_youtube(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_3.json',
            'http://www.youtube.com/watch?v=SF1Tndsfobc')

    def test_video_blip_tv(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_5.json',
            'http://blip.tv/pycon-us-videos-2009-2010-2011/pycon-2011-python-ides-panel-4901374')

    def test_video_vimeo(self):
        from plus import VideoPost as Post

        self.do_test_equal(Post,
            'sample_video_1.json',
            'http://www.vimeo.com/20743963')


class TestMultiple(TestGooglePost):
    def test_multiple_photos(self):
        from plus import GalleryPost as Post
        result = """<a href="https://lh5.googleusercontent.com/-PIH6HJqexW4/UDenK9zqRuI/AAAAAAAAAO8/jSa81lHtd_s/s640/images.jpg"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh5.googleusercontent.com/-PIH6HJqexW4/UDenK9zqRuI/AAAAAAAAAO8/jSa81lHtd_s/s640/images.jpg"\n              id="plus_gallery__0"\n              class="shashinThumbnailImage"\n              alt="images.jpg"\n              title="images.jpg"\n              />\n      </a>\n    \n  \n\n  \n\n\n  \n\n  \n    \n      <a href="https://lh4.googleusercontent.com/-PCvDAIT1nBc/UDenNq2SR4I/AAAAAAAAAPE/ez9G23m6HfY/s640/klingon.jpg"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh4.googleusercontent.com/-PCvDAIT1nBc/UDenNq2SR4I/AAAAAAAAAPE/ez9G23m6HfY/s640/klingon.jpg"\n              id="plus_gallery__1"\n              class="shashinThumbnailImage"\n              alt="klingon.jpg"\n              title="klingon.jpg"\n              />\n      </a>\n    \n  \n\n  \n\n\n</div>\n<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_img.json', result)

    def test_multiple_videos(self):
        from plus import GalleryPost as Post
        result = """<a href="#"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh4.googleusercontent.com/-MfJNeumzCbI/UDexcaNT4yI/AAAAAAAAATk/Y8u9gA4k9Wc/s640/20051210-w50s.flv.jpg"\n              id="plus_gallery__0"\n              class="shashinThumbnailImage"\n              alt="20051210-w50s.flv"\n              title="20051210-w50s.flv"\n              />\n      </a>\n      <div class="highslide-maincontent">\n      \n<iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780283748382925602" style="width: 100%; height: 100%;" ></iframe>\n\n      </div>\n    \n  \n\n  \n\n\n  \n\n  \n    \n      <a href="#"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh5.googleusercontent.com/-lLhNdxwVedw/UDeyfMG9jjI/AAAAAAAAASA/SEEauN4dP3M/s640/20051210-w50s.flv.jpg"\n              id="plus_gallery__1"\n              class="shashinThumbnailImage"\n              alt="20051210-w50s.flv"\n              title="20051210-w50s.flv"\n              />\n      </a>\n      <div class="highslide-maincontent">\n      \n<iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780284895649435186" style="width: 100%; height: 100%;" ></iframe>\n\n      </div>\n    \n  \n\n  \n\n\n</div>\n<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_vid.json', result)

    def test_single_linked(self):
        from plus import WebPagePost
        result = ''
        self.do_test_equal(WebPagePost, 'sample_webpage.json', result)


class TestPhotoContent(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh3.googleusercontent.com%2F-pO-hpo7EM7E%2FTv55RUxDaUI%2FAAAAAAAAAMk%2FW3HP0NZUdjg%2Fw288-h288%2Fcrop.png" alt="">"""
        self.do_test_equal(PhotoPost, 'pic_with_content.json', result)

    def test_photo_from_picasa_web(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh5.googleusercontent.com%2F-B-U72k6hExM%2FUAHNU_bEb4I%2FAAAAAAAAHDg%2FhxWdDTvWnNY%2Fw288-h288%2F11-C-611%252B%2525281%252529.jpg" alt="">"""
        self.do_test_equal(PhotoPost, 'sample_picasa1.json', result)

    def test_photo_from_flickr(self):
        from plus import PhotoPost
        result = ''
        self.do_test_equal(PhotoPost, 'pic_flickr_with_content.json', result)

    def test_photo_from_smugmug(self):
        from plus import PhotoPost
        result = ''
        self.do_test_equal(PhotoPost, 'sample_smugmug1.json', result)


class TestVideoContent(TestGooglePost):
    def test_video_youtube(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_2.json',
            'http://www.youtube.com/watch?v=YcFHeTaS9ew')

    def test_video_blip_tv(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_4.json',
            'http://blip.tv/pycon-us-videos-2009-2010-2011/pycon-2011-hidden-treasures-in-the-standard-library-4901130')

    def test_video_vimeo(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_0.json',
            'http://www.vimeo.com/1622823')


class TestMultipleContent(TestGooglePost):
    def test_multiple_photos(self):
        from plus import GalleryPost as Post
        result = """<a href="https://lh5.googleusercontent.com/-lUEEBO4q1x0/UDeqmyEKtkI/AAAAAAAAAP4/mdmjzbPyKyw/s640/klingon.jpg"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh5.googleusercontent.com/-lUEEBO4q1x0/UDeqmyEKtkI/AAAAAAAAAP4/mdmjzbPyKyw/s640/klingon.jpg"\n              id="plus_gallery__0"\n              class="shashinThumbnailImage"\n              alt="klingon.jpg"\n              title="klingon.jpg"\n              />\n      </a>\n    \n  \n\n  \n\n\n  \n\n  \n    \n      <a href="https://lh5.googleusercontent.com/-EwsGU3ab370/UDeqvIpR_XI/AAAAAAAAAQA/k_ENNAjp8TQ/s640/IMG-20120708-00039.jpg"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh5.googleusercontent.com/-EwsGU3ab370/UDeqvIpR_XI/AAAAAAAAAQA/k_ENNAjp8TQ/s640/IMG-20120708-00039.jpg"\n              id="plus_gallery__1"\n              class="shashinThumbnailImage"\n              alt="IMG-20120708-00039.jpg"\n              title="IMG-20120708-00039.jpg"\n              />\n      </a>\n    \n  \n\n  \n\n\n</div>\n<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_img1.json', result)

    def test_multiple_videos(self):
        from plus import GalleryPost as Post
        result = """<a href="#"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh4.googleusercontent.com/-MfJNeumzCbI/UDexcaNT4yI/AAAAAAAAATk/Y8u9gA4k9Wc/s640/20051210-w50s.flv.jpg"\n              id="plus_gallery__0"\n              class="shashinThumbnailImage"\n              alt="20051210-w50s.flv"\n              title="20051210-w50s.flv"\n              />\n      </a>\n      <div class="highslide-maincontent">\n      \n<iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780283748382925602" style="width: 100%; height: 100%;" ></iframe>\n\n      </div>\n    \n  \n\n  \n\n\n  \n\n  \n    \n      <a href="#"\n          id="plus_gallery_"\n          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"\n          class="highslide">\n          <img src="https://lh5.googleusercontent.com/-lLhNdxwVedw/UDeyfMG9jjI/AAAAAAAAASA/SEEauN4dP3M/s640/20051210-w50s.flv.jpg"\n              id="plus_gallery__1"\n              class="shashinThumbnailImage"\n              alt="20051210-w50s.flv"\n              title="20051210-w50s.flv"\n              />\n      </a>\n      <div class="highslide-maincontent">\n      \n<iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780284895649435186" style="width: 100%; height: 100%;" ></iframe>\n\n      </div>\n    \n  \n\n  \n\n\n</div>\n<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_vid.json', result)

    def test_single_linked(self):
        from plus import WebPagePost
        result = ''
        self.do_test_equal(WebPagePost, 'sample_webpage.json', result)


class TestShare(TestGooglePost):
    def test_share(self):
        from plus import TextPost
        gdata = self.load_data('sample_share.json')
        post = TextPost('', gdata, {})

        self.assertTrue(gdata['object'].get('id', '') != '')
        self.assertTrue(gdata['annotation'] != None)


class TestUtils(TestGooglePost):
    def test_title_generation(self):
        from plus import WebPagePost
        gdata = self.load_data('sample_webpage.json')

        post = WebPagePost('', gdata, {})
        self.assertEqual("""The Freshdesk Story - How Girish Mathrubootham innovated online helpdesk software &amp; made cloud based customer support affordable""", post.title)


class TestGeocode(TestGooglePost):
    def test_post(self):
        from plus import PhotoPost
        result = """\n<div class="geocode">\n    <a href="http://maps.google.com/?ll=-7.3588039,106.4051172&q=-7.3588039,106.4051172">\n        <img src="http://maps.googleapis.com/maps/api/staticmap?center=-7.3588039,106.4051172&zoom=12&size=75x75&maptype=roadmap&markers=size:small|color:red|-7.3588039,106.4051172&sensor=false" class="alignleft">\n        \n        \n    </a>\n</div>"""
        self.do_test_equal(PhotoPost, 'pic_with_geocode.json', result, 'render_geocode')


if __name__ == '__main__':
    unittest.main()
