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
        self.config = MagicMock()
        modules = {
            'oauth2client.client': self.oauth2client_mock,
            'oauth2client.flow_from_clientsecrets':
              self.oauth2client_mock.flow_from_clientsecrets,
            'config': self.config
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

    def mock_embedly(self, expected_return_value):
        """Mock embedly object"""
        import plus

        plus.OEMBED_CONSUMER = MagicMock()
        embed = MagicMock()
        embed.getData = MagicMock(side_effect=expected_return_value)
        plus.OEMBED_CONSUMER.embed.return_value = embed


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

        self.mock_embedly([
            {u'provider_url': u'http://picasaweb.google.com/',
             u'version': u'1.0',
             u'title': u'images.jpg',
             u'url': u'https://lh5.googleusercontent.com/-PIH6HJqexW4/UDenK9zqRuI/AAAAAAAAAO8/jSa81lHtd_s/s640/images.jpg',
             u'author_name': u'Bayu Adji',
             u'height': 204, u'width': 204,
             u'thumbnail_url': u'https://lh5.googleusercontent.com/-PIH6HJqexW4/UDenK9zqRuI/AAAAAAAAAO8/jSa81lHtd_s/s640/images.jpg',
             u'thumbnail_width': 204,
             u'provider_name': u'Picasa',
             u'cache_age': 86400,
             u'type': u'photo',
             u'thumbnail_height': 204,
             u'author_url': u'https://picasaweb.google.com/111415681122206252267'},
             {u'provider_url': u'http://picasaweb.google.com/',
              u'version': u'1.0',
              u'title': u'klingon.jpg',
              u'url': u'https://lh4.googleusercontent.com/-PCvDAIT1nBc/UDenNq2SR4I/AAAAAAAAAPE/ez9G23m6HfY/s640/klingon.jpg',
              u'author_name': u'Bayu Adji',
              u'height': 144,
              u'width': 135,
              u'thumbnail_url': u'https://lh4.googleusercontent.com/-PCvDAIT1nBc/UDenNq2SR4I/AAAAAAAAAPE/ez9G23m6HfY/s640/klingon.jpg',
              u'thumbnail_width': 135,
              u'provider_name': u'Picasa',
              u'cache_age': 86400,
              u'type': u'photo',
              u'thumbnail_height': 144,
              u'author_url': u'https://picasaweb.google.com/111415681122206252267'}
            ])

        result = """<a href="https://lh5.googleusercontent.com/-PIH6HJqexW4/UDenK9zqRuI/AAAAAAAAAO8/jSa81lHtd_s/s640/images.jpg"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh5.googleusercontent.com/-PIH6HJqexW4/UDenK9zqRuI/AAAAAAAAAO8/jSa81lHtd_s/s640/images.jpg"
              id="plus_gallery__0"
              class="shashinThumbnailImage"
              alt="images.jpg"
              title="images.jpg"
              />
      </a>
    
  

  


  

  
    
      <a href="https://lh4.googleusercontent.com/-PCvDAIT1nBc/UDenNq2SR4I/AAAAAAAAAPE/ez9G23m6HfY/s640/klingon.jpg"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh4.googleusercontent.com/-PCvDAIT1nBc/UDenNq2SR4I/AAAAAAAAAPE/ez9G23m6HfY/s640/klingon.jpg"
              id="plus_gallery__1"
              class="shashinThumbnailImage"
              alt="klingon.jpg"
              title="klingon.jpg"
              />
      </a>
    
  

  


</div>
<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_img.json', result)

    def test_multiple_videos(self):
        from plus import GalleryPost as Post

        self.mock_embedly([
            {
            u'provider_url': u'http://picasaweb.google.com/',
            u'title': u'20051210-w50s.flv',
            u'type': u'video',
            u'html': u'iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780283748382925602" style="width: 100%; height: 100%;" ></iframe>',
            u'author_name': u'Bayu Adji',
            u'height': 360,
            u'width': 480,
            u'version': u'1.0',
            u'thumbnail_width': 480,
            u'provider_name': u'Picasa',
            u'cache_age': 3600,
            u'thumbnail_url': u'https://lh4.googleusercontent.com/-MfJNeumzCbI/UDexcaNT4yI/AAAAAAAAATk/Y8u9gA4k9Wc/s640/20051210-w50s.flv.jpg',
            u'thumbnail_height': 360,
            u'author_url': u'https://picasaweb.google.com/111415681122206252267'},
            {u'provider_url': u'http://picasaweb.google.com/',
            u'title': u'20051210-w50s.flv',
            u'type': u'video',
            u'html': u'iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780284895649435186" style="width: 100%; height: 100%;" ></iframe>',
            u'author_name': u'Bayu Adji',
            u'height': 360,
            u'width': 480,
            u'version': u'1.0',
            u'thumbnail_width': 480,
            u'provider_name': u'Picasa',
            u'cache_age': 3600,
            u'thumbnail_url': u'https://lh5.googleusercontent.com/-lLhNdxwVedw/UDeyfMG9jjI/AAAAAAAAASA/SEEauN4dP3M/s640/20051210-w50s.flv.jpg',
            u'thumbnail_height': 360,
            u'author_url': u'https://picasaweb.google.com/111415681122206252267'}])

        result = """<a href="#"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh4.googleusercontent.com/-MfJNeumzCbI/UDexcaNT4yI/AAAAAAAAATk/Y8u9gA4k9Wc/s640/20051210-w50s.flv.jpg"
              id="plus_gallery__0"
              class="shashinThumbnailImage"
              alt="20051210-w50s.flv"
              title="20051210-w50s.flv"
              />
      </a>
      <div class="highslide-maincontent">
      iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780283748382925602" style="width: 100%; height: 100%;" ></iframe>
      </div>
    
  

  


  

  
    
      <a href="#"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh5.googleusercontent.com/-lLhNdxwVedw/UDeyfMG9jjI/AAAAAAAAASA/SEEauN4dP3M/s640/20051210-w50s.flv.jpg"
              id="plus_gallery__1"
              class="shashinThumbnailImage"
              alt="20051210-w50s.flv"
              title="20051210-w50s.flv"
              />
      </a>
      <div class="highslide-maincontent">
      iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780284895649435186" style="width: 100%; height: 100%;" ></iframe>
      </div>
    
  

  


</div>
<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_vid.json', result)

    def test_single_linked(self):
        from plus import WebPagePost

        self.mock_embedly([
            {"provider_url": "http://blog.freshdesk.com",
             "description": "Bio My name is Girish Mathrubootham and I am the Founder and CEO of Freshdesk. I am 36 years old, married and live with my wife and two boys in Chennai, India. This is the story of how I quit my comfortable job and launched my own startup. Hope you like it.",
             "title": "The Freshdesk Story - Girish talks about the evolution of his Online Helpdesk Software",
             "url": "http://blog.freshdesk.com/the-freshdesk-story-how-a-simple-comment-on-h-0/",
             "thumbnail_width": 600,
             "thumbnail_url": "http://50.116.32.94/wp-content/uploads/2011/03/freshdesk_story.png",
             "version": "1.0",
             "provider_name": "Freshdesk",
             "type": "link",
             "thumbnail_height": 322}
            ])

        result = """<h4><a href="http://blog.freshdesk.com/the-freshdesk-story-how-a-simple-comment-on-h-0/#.UDe240hoWHd">The Freshdesk Story - Girish talks about the evolution of his Online Helpdesk Software</a></h4>

<table>
  <tr>
    <td>

      <blockquote cite="http://blog.freshdesk.com/the-freshdesk-story-how-a-simple-comment-on-h-0/#.UDe240hoWHd">
        Bio My name is Girish Mathrubootham and I am the Founder and CEO of Freshdesk. I am 36 years old, married and live with my wife and two boys in Chennai, India. This is the story of how I quit my comfortable job and launched my own startup. Hope you like it.
      </blockquote>

    </td>
    <td>
  
      <img src=\'http://50.116.32.94/wp-content/uploads/2011/03/freshdesk_story.png\'>
  
    </td>
  </tr>
</table>"""

        self.do_test_equal(WebPagePost, 'sample_webpage.json', result)


class TestPhotoContent(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh3.googleusercontent.com%2F-pO-hpo7EM7E%2FTv55RUxDaUI%2FAAAAAAAAAMk%2FW3HP0NZUdjg%2Fw288-h288%2Fcrop.png" alt="">"""
        self.do_test_equal(PhotoPost, 'pic_with_content.json', result)

    def test_photo_from_picasa_web(self):
        from plus import PhotoPost
        result = """<img class="alignnone" src="https://images0-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&gadget=a&resize_h=100&url=https%3A%2F%2Flh5.googleusercontent.com%2F-B-U72k6hExM%2FUAHNU_bEb4I%2FAAAAAAAAHDg%2FhxWdDTvWnNY%2Fw288-h288%2F11-C-611%252B%2525281%252529.jpg" alt="">"""
        self.do_test_equal(PhotoPost, 'sample_picasa_with_content.json', result)

    def test_photo_from_flickr(self):
        from plus import PhotoPost
        result = ''
        self.do_test_equal(PhotoPost, 'pic_flickr_with_content.json', result)

    def test_photo_from_smugmug(self):
        from plus import PhotoPost
        result = ''
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

        self.mock_embedly([
            {u'provider_url': u'http://picasaweb.google.com/',
             u'version': u'1.0',
             u'title': u'klingon.jpg',
             u'url': u'https://lh5.googleusercontent.com/-lUEEBO4q1x0/UDeqmyEKtkI/AAAAAAAAAP4/mdmjzbPyKyw/s640/klingon.jpg',
             u'author_name': u'Bayu Adji',
             u'height': 144,
             u'width': 135,
             u'thumbnail_url': u'https://lh5.googleusercontent.com/-lUEEBO4q1x0/UDeqmyEKtkI/AAAAAAAAAP4/mdmjzbPyKyw/s640/klingon.jpg',
             u'thumbnail_width': 135,
             u'provider_name': u'Picasa',
             u'cache_age': 86400,
             u'type': u'photo',
             u'thumbnail_height': 144,
             u'author_url': u'https://picasaweb.google.com/111415681122206252267'},
            {u'provider_url': u'http://picasaweb.google.com/',
             u'version': u'1.0',
             u'title': u'IMG-20120708-00039.jpg',
             u'url': u'https://lh5.googleusercontent.com/-EwsGU3ab370/UDeqvIpR_XI/AAAAAAAAAQA/k_ENNAjp8TQ/s640/IMG-20120708-00039.jpg',
             u'author_name': u'Bayu Adji',
             u'height': 480,
             u'width': 640,
             u'thumbnail_url': u'https://lh5.googleusercontent.com/-EwsGU3ab370/UDeqvIpR_XI/AAAAAAAAAQA/k_ENNAjp8TQ/s640/IMG-20120708-00039.jpg',
             u'thumbnail_width': 640,
             u'provider_name': u'Picasa',
             u'cache_age': 86400,
             u'type': u'photo',
             u'thumbnail_height': 480,
             u'author_url': u'https://picasaweb.google.com/111415681122206252267'}
            ])

        result = """<a href="https://lh5.googleusercontent.com/-lUEEBO4q1x0/UDeqmyEKtkI/AAAAAAAAAP4/mdmjzbPyKyw/s640/klingon.jpg"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh5.googleusercontent.com/-lUEEBO4q1x0/UDeqmyEKtkI/AAAAAAAAAP4/mdmjzbPyKyw/s640/klingon.jpg"
              id="plus_gallery__0"
              class="shashinThumbnailImage"
              alt="klingon.jpg"
              title="klingon.jpg"
              />
      </a>
    
  

  


  

  
    
      <a href="https://lh5.googleusercontent.com/-EwsGU3ab370/UDeqvIpR_XI/AAAAAAAAAQA/k_ENNAjp8TQ/s640/IMG-20120708-00039.jpg"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh5.googleusercontent.com/-EwsGU3ab370/UDeqvIpR_XI/AAAAAAAAAQA/k_ENNAjp8TQ/s640/IMG-20120708-00039.jpg"
              id="plus_gallery__1"
              class="shashinThumbnailImage"
              alt="IMG-20120708-00039.jpg"
              title="IMG-20120708-00039.jpg"
              />
      </a>
    
  

  


</div>
<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_img_with_content.json', result)

    def test_multiple_videos(self):
        from plus import GalleryPost as Post

        self.mock_embedly([
            {u'provider_url': u'http://picasaweb.google.com/',
             u'title': u'20051210-w50s.flv',
             u'type': u'video',
             u'html': u'<iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780283748382925602" style="width: 100%; height: 100%;" ></iframe>',
             u'author_name': u'Bayu Adji',
             u'height': 360,
             u'width': 480,
             u'version': u'1.0',
             u'thumbnail_width': 480,
             u'provider_name': u'Picasa',
             u'cache_age': 3600,
             u'thumbnail_url': u'https://lh4.googleusercontent.com/-MfJNeumzCbI/UDexcaNT4yI/AAAAAAAAATk/Y8u9gA4k9Wc/s640/20051210-w50s.flv.jpg',
             u'thumbnail_height': 360,
             u'author_url': u'https://picasaweb.google.com/111415681122206252267'},
            {u'provider_url': u'http://picasaweb.google.com/',
             u'title': u'20051210-w50s.flv',
             u'type': u'video',
             u'html': u'<iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780284895649435186" style="width: 100%; height: 100%;" ></iframe>',
             u'author_name': u'Bayu Adji',
             u'height': 360,
             u'width': 480,
             u'version': u'1.0',
             u'thumbnail_width': 480,
             u'provider_name': u'Picasa',
             u'cache_age': 3600,
             u'thumbnail_url': u'https://lh5.googleusercontent.com/-lLhNdxwVedw/UDeyfMG9jjI/AAAAAAAAASA/SEEauN4dP3M/s640/20051210-w50s.flv.jpg',
             u'thumbnail_height': 360,
             u'author_url': u'https://picasaweb.google.com/111415681122206252267'}
            ])
        result = """<a href="#"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh4.googleusercontent.com/-MfJNeumzCbI/UDexcaNT4yI/AAAAAAAAATk/Y8u9gA4k9Wc/s640/20051210-w50s.flv.jpg"
              id="plus_gallery__0"
              class="shashinThumbnailImage"
              alt="20051210-w50s.flv"
              title="20051210-w50s.flv"
              />
      </a>
      <div class="highslide-maincontent">
      <iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780283748382925602" style="width: 100%; height: 100%;" ></iframe>
      </div>
    
  

  


  

  
    
      <a href="#"
          id="plus_gallery_"
          onclick="return hs.expand(this, { autoplay: false, slideshowGroup: \'plus_gallery_\' })"
          class="highslide">
          <img src="https://lh5.googleusercontent.com/-lLhNdxwVedw/UDeyfMG9jjI/AAAAAAAAASA/SEEauN4dP3M/s640/20051210-w50s.flv.jpg"
              id="plus_gallery__1"
              class="shashinThumbnailImage"
              alt="20051210-w50s.flv"
              title="20051210-w50s.flv"
              />
      </a>
      <div class="highslide-maincontent">
      <iframe src="picasaweb-oembed.appspot.com/static/embed.html#user/111415681122206252267/albumid/5780283745281083937/photoid/5780284895649435186" style="width: 100%; height: 100%;" ></iframe>
      </div>
    
  

  


</div>
<script type="text/javascript">addHSSlideshow(\'plus_gallery_\');</script>"""
        self.do_test_equal(Post, 'sample_multi_vid.json', result)

    def test_single_linked(self):
        from plus import WebPagePost

        result = """<h4><a href="http://antjanus.com/blog/web-design-tips/user-interface-usability/customize-twitter-bootstrap-into-themes/">Customize Twitter Bootstrap To Not Look Bootstrap-y - Aj freelancer</a></h4>

<table>
  <tr>
    <td>

      <blockquote cite="http://antjanus.com/blog/web-design-tips/user-interface-usability/customize-twitter-bootstrap-into-themes/">
        PLEASE, if you do use Bootstrap for just about everything be courteous to your audience and change up some of the basic variables so it doesn\'t look all the same! I just tested a really cool app and was SO disappointed that it used bootstrap. I\'m sick of seeing the same damn buttons.
      </blockquote>

    </td>
    <td>
  
      <img src=\'http://antjanus.com/assets/bootstrap-1024x421.png\'>
  
    </td>
  </tr>
</table>"""

        self.mock_embedly([
            {"provider_url": "http://antjanus.com",
             "description": "PLEASE, if you do use Bootstrap for just about everything be courteous to your audience and change up some of the basic variables so it doesn't look all the same! I just tested a really cool app and was SO disappointed that it used bootstrap. I'm sick of seeing the same damn buttons.",
             "title": "Customize Twitter Bootstrap To Not Look Bootstrap-y - Aj freelancer",
             "url": "http://antjanus.com/blog/web-design-tips/user-interface-usability/customize-twitter-bootstrap-into-themes/",
             "thumbnail_width": 1024,
             "thumbnail_url": "http://antjanus.com/assets/bootstrap-1024x421.png",
             "version": "1.0",
             "provider_name": "Antjanus",
             "type": "link", "thumbnail_height": 421}])
        self.do_test_equal(WebPagePost, 'sample_webpage_with_content.json', result)


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

        self.mock_embedly([{'title': "From mock"}])
        gdata = self.load_data('sample_webpage.json')

        post = WebPagePost('', gdata, {})
        post.render()
        self.assertEqual("""From mock""", post.title)


class TestGeocode(TestGooglePost):
    def test_post(self):
        from plus import PhotoPost
        result = """
<div class="geocode">
    <a href="http://maps.google.com/?ll=-7.3588039,106.4051172&q=-7.3588039,106.4051172">
        <img src="http://maps.googleapis.com/maps/api/staticmap?center=-7.3588039,106.4051172&zoom=12&size=75x75&maptype=roadmap&markers=size:small|color:red|-7.3588039,106.4051172&sensor=false" class="alignleft">
        
        
    </a>
</div>"""
        self.do_test_equal(PhotoPost, 'pic_with_geocode.json', result, 'render_geocode')


if __name__ == '__main__':
    unittest.main()
