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

"""Test module for plus.py

you can run the test by running:
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
                       os.path.dirname(__file__), "test_documents", filename))
        content = file_.read()
        file_.close()
        return json.loads(content)

    def do_test_equal(self, post_class, filename, result):
        """Helper for test equal"""
        gdata = self.load_data(filename)
        gid = ''
        gcomment = {}
        post = post_class(gid, gdata, gcomment)
        post.render()
        self.assertEqual(result,
                         post.content.strip())


class TestPhoto(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost

        #we need to strip, since the render add
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh3.googleusercontent.com%2F-pO-hpo7EM7E%2FTv55RUxDaUI%2FAAAAAAAAAMk%2FW3HP0NZUdjg%2Fw288-h288%2Fcrop.png" alt="">"""
        self.do_test_equal(PhotoPost, 'pic_with_content.json', result)

    def test_photo_from_picasa_web(self):
        pass

    def test_photo_from_flickr(self):
        pass

    def test_photo_from_smugmug(self):
        pass


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
        pass

    def test_multiple_videos(self):
        pass

    def test_multiple_photos_and_videos(self):
        pass

    def test_single_linke(self):
        pass


class TestPhotoContent(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost

        #we need to strip, since the render add
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh3.googleusercontent.com%2F-pO-hpo7EM7E%2FTv55RUxDaUI%2FAAAAAAAAAMk%2FW3HP0NZUdjg%2Fw288-h288%2Fcrop.png" alt="">"""
        self.do_test_equal(PhotoPost, 'pic_with_content.json', result)

    def test_photo_from_picasa_web(self):
        pass

    def test_photo_from_flickr(self):
        pass

    def test_photo_from_smugmug(self):
        pass


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
        pass

    def test_multiple_videos(self):
        pass

    def test_multiple_photos_and_videos(self):
        pass

    def test_single_linke(self):
        pass


class TestPhotoShare(TestGooglePost):
    def test_photo_from_google_plus(self):
        pass
    
    def test_photo_from_picasa_web(self):
        pass

    def test_photo_from_flickr(self):
        pass

    def test_photo_from_smugmug(self):
        pass


class TestVideoShare(TestGooglePost):
    def test_video_youtube(self):
        pass

    def test_video_blip_tv(self):
        pass

    def test_video_vimeo(self):
        pass


class TestMultipleShare(TestGooglePost):
    def test_multiple_photos(self):
        pass

    def test_multiple_videos(self):
        pass

    def test_multiple_photos_and_videos(self):
        pass

    def test_single_linke(self):
        pass


class TestUtils(TestGooglePost):
    def test_title_generation(self):
        pass


class TestGeocode(TestGooglePost):
    def test_post(self):
        pass


if __name__ == '__main__':
    unittest.main()
