import io
import unittest
from unittest import mock

from bigbluebutton_api_python import AsyncBigBlueButton, BigBlueButton
from bigbluebutton_api_python.exception import BBBException
from bigbluebutton_api_python.parameters import BBBModule
from bigbluebutton_api_python.util import UrlBuilder

SECRET = "639259d4-9dd8-4b25-bf01-95f9567eaf4b"


class FakeResponse(io.BytesIO):
    def __init__(self, body, content_type="text/xml;charset=utf-8"):
        super().__init__(body.encode())
        self.content_type = content_type

    def getheader(self, name):
        return self.content_type


class UrlBuilderTest(unittest.TestCase):
    def test_checksum_matches_bbb_docs_example(self):
        # example from the official BBB API docs
        url = UrlBuilder("https://bbb.example.com", SECRET).buildUrl(
            "create", {"name": "Test Meeting", "meetingID": "abc123", "attendeePW": "111222", "moderatorPW": "333444"})
        self.assertTrue(url.startswith("https://bbb.example.com/bigbluebutton/api/create?name=Test+Meeting&"))
        self.assertTrue(url.endswith("checksum=1fcbb0c4fc1f039f73aa6d697d2db9ba7f803f17"))

    def test_sha256_and_bad_algorithm(self):
        url = UrlBuilder("bbb.example.com", SECRET, "sha256").buildUrl("getMeetings")
        self.assertEqual(len(url.split("checksum=")[1]), 64)
        self.assertRaises(ValueError, UrlBuilder, "bbb.example.com", SECRET, "md5")


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.bbb = BigBlueButton("https://bbb.example.com/bigbluebutton/api/", SECRET)

    def test_join_requires_role_or_password(self):
        self.assertRaises(ValueError, self.bbb.get_join_meeting_url, "Ann", "m1")
        url = self.bbb.get_join_meeting_url("Ann", "m1", role=BigBlueButton.MODERATOR)
        self.assertIn("role=MODERATOR", url)

    @mock.patch("bigbluebutton_api_python.bigbluebutton.urlopen")
    def test_create_does_not_leak_params_between_calls(self, urlopen):
        urlopen.side_effect = lambda *a, **k: FakeResponse(
            "<response><returncode>SUCCESS</returncode><meetingID>x</meetingID></response>")
        self.bbb.create_meeting("m1", meta={"a": "1"})
        self.bbb.create_meeting("m2")
        self.assertNotIn("meta_a", urlopen.call_args[0][0])

    @mock.patch("bigbluebutton_api_python.bigbluebutton.urlopen")
    def test_failed_returncode_raises(self, urlopen):
        urlopen.return_value = FakeResponse(
            "<response><returncode>FAILED</returncode><messageKey>notFound</messageKey>"
            "<message>no meeting</message></response>")
        with self.assertRaises(BBBException) as cm:
            self.bbb.get_meeting_info("missing")
        self.assertEqual(cm.exception.key, "notFound")

    @mock.patch("bigbluebutton_api_python.bigbluebutton.urlopen")
    def test_json_response_with_charset(self, urlopen):
        urlopen.return_value = FakeResponse('{"response": {"returncode": "SUCCESS", "tracks": []}}',
                                            "application/json;charset=UTF-8")
        self.assertEqual(self.bbb.get_recording_text_tracks("r1").get_field("tracks"), [])


class AsyncClientTest(unittest.IsolatedAsyncioTestCase):
    @mock.patch("bigbluebutton_api_python.bigbluebutton.urlopen")
    async def test_calls_are_awaitable_and_errors_propagate(self, urlopen):
        bbb = AsyncBigBlueButton("https://bbb.example.com", SECRET)
        self.assertIn("role=VIEWER", bbb.get_join_meeting_url("Bob", "m1", role=BigBlueButton.VIEWER))
        urlopen.return_value = FakeResponse("<response><returncode>SUCCESS</returncode><running>true</running></response>")
        self.assertTrue((await bbb.is_meeting_running("m1")).is_meeting_running())
        urlopen.return_value = FakeResponse(
            "<response><returncode>FAILED</returncode><messageKey>notFound</messageKey><message>x</message></response>")
        with self.assertRaises(BBBException):
            await bbb.get_meeting_info("missing")


class BBBModuleTest(unittest.TestCase):
    def test_escapes_and_encodes_files(self):
        m = BBBModule()
        m.add_slide(BBBModule.URL, 'https://x/a.pdf?a=1&b=2')
        m.add_slide(BBBModule.FILE, __file__)
        xml = m.to_xml()
        self.assertIn('url="https://x/a.pdf?a=1&amp;b=2"', xml)
        self.assertIn('name="test_api.py"', xml)


if __name__ == "__main__":
    unittest.main()
