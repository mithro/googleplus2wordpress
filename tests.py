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
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mock import patch, MagicMock, Mock


class TestGooglePost(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.oauth2client_mock = MagicMock()
        self.oauth2client_mock.flow_from_clientsecrets = Mock()
        self.config = MagicMock()
        self.config.EMBEDLY_KEY = ''
        modules = {
            'oauth2client.client': self.oauth2client_mock,
            'oauth2client.flow_from_clientsecrets':
              self.oauth2client_mock.flow_from_clientsecrets,
            'config': self.config
        }

        self.module_patcher = patch.dict('sys.modules', modules)
        self.module_patcher.start()
        self.maxDiff = None

    def tearDown(self):
        self.module_patcher.stop()

    def load_data(self, filename, type="json"):
        """
        Load the file data, from json into gdata.
        """
        file_ = open(os.path.join(
            os.path.dirname(__file__),
            "test_documents", filename))

        content = file_.read()
        file_.close()

        if type == 'json':
            return json.loads(content)

        return content

    def do_test_equal(self, post_class, filename, result,
                      method=None, equal_function='assertEqual'):
        """Helper for test equal"""
        gdata = self.load_data(filename)
        gid = ''
        gcomment = {}
        post = post_class(gid, gdata, gcomment)
        post.render()
        result_tmpl = getattr(post, method, 'ERROR')() if method else post.content.strip()

        getattr(self, equal_function, None)(
            result,
            result_tmpl)

    def mock_embedly(self, expected_return_value):
        """Mock embedly object"""
        import plus
        if not isinstance(expected_return_value, (list, tuple)):
            expected_return_value = [expected_return_value, ]

        plus.OEMBED_CONSUMER = MagicMock()
        embed = MagicMock()
        embed.getData = MagicMock(side_effect=expected_return_value)
        plus.OEMBED_CONSUMER.embed.return_value = embed


class TestPhoto(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost

        #we need to strip, since the render add
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh5.googleusercontent.com%2F-YhGQ2IKWJok%2FUDR4WL8APXI%2FAAAAAAAAAOI%2FdjbWuClePMk%2Fs0-d%2F14-05-07_1132.jpg" alt="">"""
        self.mock_embedly({})
        self.do_test_equal(PhotoPost, 'sample_pic_without_content.json', result)

    def test_photo_from_picasa_web(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh6.googleusercontent.com%2F-D0vjgEuIKFM%2FT-rhhY-iBbI%2FAAAAAAAAIJw%2FSUL6I7p1Sh4%2Fw288-h288%2FSkyline%252BWinterfest.jpg" alt="">"""
        self.mock_embedly({})
        self.do_test_equal(PhotoPost, 'sample_picasa.json', result)

    def test_photo_from_flickr(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="http://farm8.staticflickr.com/7061/6987228783_2b951598c9_s.jpg" alt="Infinity London Underground EXPLORED #1 My Top 40 Click Best viewed hereClick Please check out my new group City and Architecture No images or links in comments, many thanks!!!">"""

        self.mock_embedly(self.load_data('embedly_flickr.json'))
        self.do_test_equal(PhotoPost, 'sample_pic_flickr_without_content.json', result)

    def test_photo_from_smugmug(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="http://fotoeffects.smugmug.com/Daily-shots-for-the-dailies/Dailies/i-VNkmwF6/0/M/DSC6450-M.jpg" alt="">"""
        self.mock_embedly(self.load_data('embedly_smugmug.json'))
        self.do_test_equal(PhotoPost, 'sample_smugmug.json', result)


class TestVideo(TestGooglePost):
    def test_video_youtube(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_youtube.json',
            'http://www.youtube.com/watch?v=SF1Tndsfobc')

    def test_video_blip_tv(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_blip.json',
            'http://blip.tv/pycon-us-videos-2009-2010-2011/pycon-2011-python-ides-panel-4901374')

    def test_video_vimeo(self):
        from plus import VideoPost as Post

        self.do_test_equal(Post,
            'sample_video_vimeo.json',
            'http://www.vimeo.com/20743963')


class TestMultiple(TestGooglePost):
    def test_multiple_photos(self):
        from plus import GalleryPost as Post

        self.mock_embedly(self.load_data('embedly_multiple_photos.json', type='json'))

        result = self.load_data("result_multiple_photos.html", type='html')
        self.do_test_equal(Post, 'sample_multi_img.json', result, equal_function='assertMultiLineEqual')

    def test_multiple_videos(self):
        from plus import GalleryPost as Post

        self.mock_embedly(self.load_data("embedly_multiple_videos.json", type='json'))

        result = self.load_data('result_multiple_videos.html', type='html')
        self.do_test_equal(Post, 'sample_multi_vid.json', result, equal_function='assertMultiLineEqual')

    def test_single_linked(self):
        from plus import WebPagePost

        self.mock_embedly(self.load_data('embedly_single_linked.json', type='json'))

        result = self.load_data('result_single_linked.html', type='html')

        self.do_test_equal(WebPagePost, 'sample_webpage.json', result, equal_function='assertMultiLineEqual')

    def test_multiple_photo_video(self):
        from plus import GalleryPost as Post

        self.do_test_equal(Post, 'sample_photo_video_content.json', '', equal_function='assertMultiLineEqual')


class TestPhotoContent(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh3.googleusercontent.com%2F-pO-hpo7EM7E%2FTv55RUxDaUI%2FAAAAAAAAAMk%2FW3HP0NZUdjg%2Fw288-h288%2Fcrop.png" alt="">"""

        self.mock_embedly({})
        self.do_test_equal(PhotoPost, 'sample_pic_with_content.json', result)

    def test_photo_from_picasa_web(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh5.googleusercontent.com%2F-B-U72k6hExM%2FUAHNU_bEb4I%2FAAAAAAAAHDg%2FhxWdDTvWnNY%2Fw288-h288%2F11-C-611%252B%2525281%252529.jpg" alt="">"""
        self.mock_embedly({})
        self.do_test_equal(PhotoPost, 'sample_picasa_with_content.json', result)

    def test_photo_from_flickr(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="http://farm8.staticflickr.com/7061/6987228783_2b951598c9_s.jpg" alt="Infinity London Underground EXPLORED #1 My Top 40 Click Best viewed hereClick Please check out my new group City and Architecture No images or links in comments, many thanks!!!">"""
        #self.mock_embedly({})

        self.mock_embedly(self.load_data('embedly_flickr_with_content.json'))
        self.do_test_equal(PhotoPost, 'sample_pic_flickr_with_content.json', result)

    def test_photo_from_smugmug(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="http://fotoeffects.smugmug.com/Daily-shots-for-the-dailies/Dailies/i-VNkmwF6/0/M/DSC6450-M.jpg" alt="">"""
        self.mock_embedly(self.load_data('embedly_smug_mug_with_content.json'))
        self.do_test_equal(PhotoPost, 'sample_smugmug_with_content.json', result)


class TestVideoContent(TestGooglePost):
    def test_video_youtube(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_youtube_with_content.json',
            'http://www.youtube.com/watch?v=YcFHeTaS9ew')

    def test_video_blip_tv(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_blip_with_content.json',
            'http://blip.tv/pycon-us-videos-2009-2010-2011/pycon-2011-hidden-treasures-in-the-standard-library-4901130')

    def test_video_vimeo(self):
        from plus import VideoPost as Post
        self.do_test_equal(Post,
            'sample_video_vimeo_with_content.json',
            'http://www.vimeo.com/1622823')


class TestMultipleContent(TestGooglePost):
    def test_multiple_photos(self):
        from plus import GalleryPost as Post

        self.mock_embedly(self.load_data('embedly_multiple_photos_content.json'))

        result = self.load_data('result_multiple_photos_with_content.html', type='html')
        self.do_test_equal(Post, 'sample_multi_img_with_content.json', result, equal_function='assertMultiLineEqual')

    def test_multiple_videos(self):
        from plus import GalleryPost as Post

        self.mock_embedly(self.load_data('embedly_multiple_videos_content.json'))
        result = self.load_data('result_multiple_videos_content.html', type='html')
        self.do_test_equal(Post, 'sample_multi_vid.json', result, equal_function='assertMultiLineEqual')

    def test_single_linked(self):
        from plus import WebPagePost

        result = self.load_data('result_single_linked_content.html', type="html")

        self.mock_embedly(self.load_data('embedly_linked_content.json'))
        self.do_test_equal(WebPagePost, 'sample_webpage_with_content.json', result, equal_function='assertMultiLineEqual')


class TestShare(TestGooglePost):
    def test_share(self):
        from plus import TextPost
        gdata = self.load_data('sample_share.json')
        post = TextPost('', gdata, {})

        self.assertTrue(gdata['object'].get('id', '') != '')
        self.assertTrue(gdata['annotation'] != None)

    def test_linked_share(self):
        from plus import TextPost
        gdata = self.load_data('sample_link_share.json')
        post = TextPost('', gdata, {})
        post.render()

        self.assertIsNotNone(gdata['object']['id'])
        self.assertEqual('', gdata['annotation'])

    def test_pic_share(self):
        from plus import TextPost
        gdata = self.load_data('sample_pic_share.json')
        post = TextPost('', gdata, {})
        post.render()

        self.assertIsNotNone(gdata['object']['id'])
        self.assertEqual('', gdata['annotation'])

    def test_video_share(self):
        from plus import TextPost
        gdata = self.load_data('sample_video_share.json')
        post = TextPost('', gdata, {})
        post.render()

        self.assertIsNotNone(gdata['object']['id'])
        self.assertEqual('', gdata['annotation'])


class TestUtils(TestGooglePost):
    def test_title_generation(self):
        from plus import WebPagePost

        self.mock_embedly([{'title': "From mock"}])
        gdata = self.load_data('sample_webpage.json')

        post = WebPagePost('', gdata, {})
        post.render()
        self.assertMultiLineEqual("""From mock""", post.title)


class TestGeocode(TestGooglePost):
    def test_post(self):
        from plus import PhotoPost
        result = self.load_data('result_geocode.html', type='html')
        self.mock_embedly({})
        self.do_test_equal(PhotoPost, 'sample_pic_with_geocode.json', result, 'render_geocode')


if __name__ == '__main__':
    unittest.main()
