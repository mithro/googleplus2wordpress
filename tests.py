import json
import os
import unittest

from mock import patch, MagicMock, Mock

__author__ = 'bayuadji@gmail.com'


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
        file_ = open(os.path.join(os.path.dirname(__file__),
                                  "test_documents",
                                  filename))
        content = file_.read()
        file_.close()
        return json.loads(content)


class TestPhoto(TestGooglePost):
    def test_photo_from_google_plus(self):
        from plus import PhotoPost

        gdata = self.load_data('pic_without_content.json')
        gid = ''
        gcomment = {}
        photo_post = PhotoPost(gid, gdata, gcomment)
        photo_post.render()
        #we need to strip, since the render add
        result = ('<img class="alignnone" '
            'src="https://images0-focus-opensocial.googleusercontent.com'
            '/gadgets/proxy?container=focus&gadget'
            '=a&resize_h=100&url=https%3A%2F%2Flh5.googleusercontent.com%2F-'
            'YhGQ2IKWJok%2FUDR4WL8APXI%2FAAAAAAAAAOI'
            '%2FdjbWuClePMk%2Fs0-d%2F14-05-07_1132.jpg" alt="">')

        self.assertEqual(result,
                         photo_post.content.strip())

    def test_photo_from_picasa_web(self):
        pass

    def test_photo_from_flickr(self):
        pass

    def test_photo_from_smugmug(self):
        pass


class TestVideo(TestGooglePost):
    def test_video_youtube(self):
        pass

    def test_video_blip_tv(self):
        pass

    def test_video_vimeo(self):
        pass


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

        gdata = self.load_data('pic_with_content.json')
        gid = ''
        gcomment = {}
        photo_post = PhotoPost(gid, gdata, gcomment)
        photo_post.render()
        #we need to strip, since the render add
        result = ('<img class="alignnone" src="https://images0-'
                  'focus-opensocial.googleusercontent.com/'
                  'gadgets/proxy?container=focus&gadget=a&'
                  'resize_h=100&url=https%3A%2F%2Flh3.'
                  'googleusercontent.com%2F-pO-hpo7EM7E%2'
                  'FTv55RUxDaUI%2FAAAAAAAAAMk%2FW3HP0NZUdjg%2Fw'
                  '288-h288%2Fcrop.png" alt="">')
        self.assertEqual(result,
                         photo_post.content.strip())

    def test_photo_from_picasa_web(self):
        pass

    def test_photo_from_flickr(self):
        pass

    def test_photo_from_smugmug(self):
        pass


class TestVideoContent(TestGooglePost):
    def test_video_youtube(self):
        pass

    def test_video_blip_tv(self):
        pass

    def test_video_vimeo(self):
        pass


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
        from plus import PhotoPost

        gdata = {'object':
                 {'content': '',
                  'attachments': [{'image': {'url':'http://test'},
                                   'fullImage':
                                     {'url': 'http://fullimage',
                                      'content': 'test'}}]
                    }
                }
        gid = ''
        gcomment = {}
        photo_post = PhotoPost(gid, gdata, gcomment)
        photo_post.render()
        #we need to strip, since the render add
        result = '<img class="alignnone" src="http://test" alt="test">'
        self.assertEqual(result,
                         photo_post.content.strip())

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
