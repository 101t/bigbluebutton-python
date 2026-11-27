"""Every endpoint parsed from the example responses in the official BBB 4.0 API docs
(docs/docs/development/api.md on the v4.0.x-release branch)."""
import asyncio
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

from bigbluebutton_api_python import AsyncBigBlueButton, BigBlueButton
from bigbluebutton_api_python.exception import BBBException
from bigbluebutton_api_python.parameters import BBBModule
from test_api import SECRET, FakeResponse

CREATE = """<response>
  <returncode>SUCCESS</returncode>
  <meetingID>Test</meetingID>
  <internalMeetingID>640ab2bae07bedc4c163f679a746f7ab7fb5d1fa-1531155809613</internalMeetingID>
  <parentMeetingID>bbb-none</parentMeetingID>
  <attendeePW>ap</attendeePW>
  <moderatorPW>mp</moderatorPW>
  <createTime>1531155809613</createTime>
  <voiceBridge>70757</voiceBridge>
  <dialNumber>613-555-1234</dialNumber>
  <createDate>Mon Jul 09 17:03:29 UTC 2018</createDate>
  <hasUserJoined>false</hasUserJoined>
  <duration>0</duration>
  <hasBeenForciblyEnded>false</hasBeenForciblyEnded>
  <messageKey>duplicateWarning</messageKey>
  <message>This conference was already in existence and may currently be in progress.</message>
</response>"""

MEETING_INFO = """<response>
	<returncode>SUCCESS</returncode>
	<meetingName>Anton G's Room</meetingName>
	<meetingID>gbesu6dht08uobpislzqxsizjzihn87cmewqyacs</meetingID>
	<internalMeetingID>a0715c95000a2bcb90604ecc7097dbc94592c690-1715261728123</internalMeetingID>
	<createTime>1715261728123</createTime>
	<createDate>Thu May 09 13:35:28 UTC 2024</createDate>
	<voiceBridge>66052</voiceBridge>
	<dialNumber>613-555-1234</dialNumber>
	<attendeePW>1umEM3ic</attendeePW>
	<moderatorPW>V91JirCa</moderatorPW>
	<running>true</running>
	<duration>0</duration>
	<hasUserJoined>true</hasUserJoined>
	<recording>true</recording>
	<hasBeenForciblyEnded>false</hasBeenForciblyEnded>
	<startTime>1715261728142</startTime>
	<endTime>0</endTime>
	<participantCount>1</participantCount>
	<listenerCount>0</listenerCount>
	<voiceParticipantCount>1</voiceParticipantCount>
	<videoCount>1</videoCount>
	<maxUsers>0</maxUsers>
	<moderatorCount>1</moderatorCount>
	<attendees>
		<attendee>
			<userID>w_ftcrsyuh44oj</userID>
			<fullName>Anton G</fullName>
			<role>MODERATOR</role>
			<isPresenter>true</isPresenter>
			<isListeningOnly>false</isListeningOnly>
			<hasJoinedVoice>true</hasJoinedVoice>
			<hasVideo>true</hasVideo>
			<clientType>HTML5</clientType>
			<customdata></customdata>
		</attendee>
	</attendees>
	<metadata>
		<bbb-origin-version>summit2024-6d8120x</bbb-origin-version>
		<bbb-origin>greenlight</bbb-origin>
	</metadata>
	<isBreakout>false</isBreakout>
</response>"""

MEETING = """<meeting>
      <meetingName>Demo Meeting</meetingName>
      <meetingID>Demo Meeting</meetingID>
      <internalMeetingID>183f0bf3a0982a127bdb8161e0c44eb696b3e75c-1531241258036</internalMeetingID>
      <createTime>1531241258036</createTime>
      <createDate>Tue Jul 10 16:47:38 UTC 2018</createDate>
      <voiceBridge>70066</voiceBridge>
      <dialNumber>613-555-1234</dialNumber>
      <attendeePW>ap</attendeePW>
      <moderatorPW>mp</moderatorPW>
      <running>false</running>
      <duration>0</duration>
      <hasUserJoined>false</hasUserJoined>
      <recording>false</recording>
      <hasBeenForciblyEnded>false</hasBeenForciblyEnded>
      <startTime>1531241258074</startTime>
      <endTime>0</endTime>
      <participantCount>0</participantCount>
      <listenerCount>0</listenerCount>
      <voiceParticipantCount>0</voiceParticipantCount>
      <videoCount>0</videoCount>
      <maxUsers>0</maxUsers>
      <moderatorCount>0</moderatorCount>
      <attendees />
      <metadata />
      <isBreakout>false</isBreakout>
    </meeting>"""

RECORDING = """<recording>
         <recordID>ffbfc4cc24428694e8b53a4e144f414052431693-%s</recordID>
         <meetingID>c637ba21adcd0191f48f5c4bf23fab0f96ed5c18</meetingID>
         <internalMeetingID>ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124</internalMeetingID>
         <name>Fred's Room</name>
         <isBreakout>false</isBreakout>
         <published>true</published>
         <state>published</state>
         <startTime>1530718721124</startTime>
         <endTime>1530718810456</endTime>
         <participants>3</participants>
         <metadata>
            <isBreakout>false</isBreakout>
            <meetingName>Fred's Room</meetingName>
            <gl-listed>false</gl-listed>
         </metadata>
         <playback>
            <format>
               <type>podcast</type>
               <url>https://demo.bigbluebutton.org/podcast/x/audio.ogg</url>
               <processingTime>0</processingTime>
               <length>0</length>
            </format>
            <format>
               <type>presentation</type>
               <url>https://demo.bigbluebutton.org/playback/presentation/2.0/playback.html?meetingId=x</url>
               <processingTime>7177</processingTime>
               <length>0</length>
            </format>
         </playback>
      </recording>"""

TEXT_TRACKS = """{"response": {"returncode": "SUCCESS", "tracks": [
  {"href": "https://captions.example.com/subtitles_en-US.vtt", "kind": "subtitles", "label": "English",
   "lang": "en-US", "source": "upload"}]}}"""


def ok(body=""):
    return "<response><returncode>SUCCESS</returncode>%s</response>" % body


class BBB40ResponsesTest(unittest.TestCase):
    def setUp(self):
        self.bbb = BigBlueButton("bbb.example.com", SECRET)
        patcher = mock.patch("bigbluebutton_api_python.bigbluebutton.urlopen")
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)

    def reply(self, body, content_type="text/xml;charset=utf-8"):
        self.urlopen.side_effect = lambda *a, **k: FakeResponse(body, content_type)

    def sent(self):
        """(endpoint, query params) of the last request."""
        arg = self.urlopen.call_args[0][0]
        url = urlparse(arg if isinstance(arg, str) else arg.full_url)
        return url.path.rsplit("/", 1)[1], {k: v[0] for k, v in parse_qs(url.query).items()}

    def test_create(self):
        self.reply(CREATE)
        r = self.bbb.create_meeting("Test", params={"record": True}, meta={"origin": "lms"})
        self.assertEqual(r.get_meetingid(), "Test")
        self.assertEqual(r.get_voice_bridge(), "70757")
        self.assertEqual(r.get_message_key(), "duplicateWarning")  # warning, not an error
        endpoint, q = self.sent()
        self.assertEqual((endpoint, q["name"], q["record"], q["meta_origin"]), ("create", "Test", "true", "lms"))

    def test_create_with_slides_posts_xml(self):
        self.reply(CREATE)
        slides = BBBModule()
        slides.add_slide(BBBModule.URL, "https://example.com/deck.pdf")
        self.bbb.create_meeting("Test", slides=slides)
        request = self.urlopen.call_args[0][0]
        self.assertEqual(request.get_header("Content-type"), "application/xml")
        self.assertIn(b'<document url="https://example.com/deck.pdf" />', request.data)

    def test_join_url(self):
        url = self.bbb.get_join_meeting_url("Alice", "room-1", role=BigBlueButton.MODERATOR,
                                            params={"userdata-bbb_prefer_dark_theme": True})
        q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        self.assertEqual(q["role"], "MODERATOR")
        self.assertEqual(q["userdata-bbb_prefer_dark_theme"], "true")
        self.assertNotIn("password", q)

    def test_is_meeting_running(self):
        self.reply(ok("<running>true</running>"))
        self.assertTrue(self.bbb.is_meeting_running("test01").is_meeting_running())
        self.reply(ok("<running>false</running>"))
        self.assertFalse(self.bbb.is_meeting_running("test01").is_meeting_running())

    def test_get_meeting_info(self):
        self.reply(MEETING_INFO)
        r = self.bbb.get_meeting_info("gbesu6dht08uobpislzqxsizjzihn87cmewqyacs")
        info = r.get_meetinginfo()
        self.assertEqual(info.get_meetingname(), "Anton G's Room")
        self.assertTrue(info.is_recording())
        self.assertEqual(info.get_participantcount(), 1)
        [attendee] = r.get_attendees()
        self.assertEqual((attendee.get_fullname(), attendee.get_role()), ("Anton G", "MODERATOR"))
        self.assertTrue(attendee.has_video())

    def test_get_meetings_one_many_none(self):
        self.reply(ok("<meetings>%s</meetings>" % MEETING))
        [m] = self.bbb.get_meetings().get_meetings()
        self.assertEqual(m.get_meetingname(), "Demo Meeting")
        self.reply(ok("<meetings>%s%s</meetings>" % (MEETING, MEETING)))
        self.assertEqual(len(self.bbb.get_meetings().get_meetings()), 2)
        self.reply(ok("<meetings/><messageKey>noMeetings</messageKey><message>no meetings were found on this server</message>"))
        self.assertEqual(self.bbb.get_meetings().get_meetings(), [])

    def test_end(self):
        self.reply(ok("<messageKey>sentEndMeetingRequest</messageKey><message>A request to end the meeting was sent.</message>"))
        self.assertEqual(self.bbb.end_meeting("1234567890").get_message_key(), "sentEndMeetingRequest")
        self.assertNotIn("password", self.sent()[1])

    def test_insert_document(self):
        self.reply(ok("<message>Presentation is being uploaded</message>"))
        slides = BBBModule()
        slides.add_slide(BBBModule.URL, "https://example.com/deck.pdf")
        r = self.bbb.insert_document("Test", slides)
        self.assertEqual(r.get_message(), "Presentation is being uploaded")

    def test_insert_document_rate_limited_raises(self):
        self.reply("<response><returncode>FAILED</returncode><messageKey>rateLimitExceeded</messageKey>"
                   "<message>Too many requests</message></response>")
        with self.assertRaises(BBBException) as cm:
            self.bbb.insert_document("Test", BBBModule())
        self.assertEqual(cm.exception.key, "rateLimitExceeded")

    def test_send_chat_message(self):
        self.reply(ok("<messageKey></messageKey><message></message>"))
        self.bbb.send_chat_message("test01", "my test", user_name="System Admin")
        endpoint, q = self.sent()
        self.assertEqual((endpoint, q["meetingID"], q["message"], q["userName"]),
                         ("sendChatMessage", "test01", "my test", "System Admin"))

    def test_get_recordings_one_many_none(self):
        self.reply(ok("<recordings>%s</recordings>" % (RECORDING % "1")))
        [rec] = self.bbb.get_recordings(meeting_id="c637ba21adcd0191f48f5c4bf23fab0f96ed5c18").get_recordings()
        self.assertEqual((rec.get_name(), rec.is_published(), rec.get_playbacktype()), ("Fred's Room", True, "podcast"))
        self.assertEqual(rec.get_meta("gl-listed"), "false")
        self.reply(ok("<recordings>%s%s</recordings><totalElements>2</totalElements>" % (RECORDING % "1", RECORDING % "2")))
        r = self.bbb.get_recordings(params={"offset": 0, "limit": 2})  # pagination, BBB >= 2.6
        self.assertEqual(len(r.get_recordings()), 2)
        self.assertEqual(r.get_field("totalElements"), "2")
        self.reply(ok("<recordings></recordings><messageKey>noRecordings</messageKey><message>There are no recordings</message>"))
        self.assertEqual(self.bbb.get_recordings().get_recordings(), [])

    def test_publish_delete_update_recordings(self):
        self.reply(ok("<published>true</published>"))
        self.assertTrue(self.bbb.publish_recordings("record123,recordABC").is_published())
        self.assertEqual(self.sent()[1]["recordID"], "record123,recordABC")
        self.reply(ok("<deleted>true</deleted>"))
        self.assertTrue(self.bbb.delete_recordings("record123").is_deleted())
        self.reply(ok("<updated>true</updated>"))
        self.assertEqual(self.bbb.update_recordings("record123", meta={"title": "x"}).get_field("updated"), "true")
        self.assertEqual(self.sent()[1]["meta_title"], "x")

    def test_recording_text_tracks(self):
        self.reply(TEXT_TRACKS, "application/json")
        [track] = self.bbb.get_recording_text_tracks("r1").get_field("tracks")
        self.assertEqual(track["lang"], "en-US")

    def test_put_recording_text_track(self):
        self.reply('{"response": {"messageKey": "upload_text_track_success", "message": "Text track uploaded '
                   'successfully", "recordId": "baz", "returncode": "SUCCESS"}}', "application/json")
        r = self.bbb.put_recording_text_track("baz", "subtitles", "en-US", label="English", file_path=__file__)
        self.assertEqual(r.get_message_key(), "upload_text_track_success")
        self.assertIn(b'filename="test_bbb40_responses.py"', self.urlopen.call_args[0][0].data)

    def test_put_recording_text_track_failure_reported_as_success_raises(self):
        # BBB answers a failed upload with returncode SUCCESS; the client must not swallow it
        self.reply('{"response": {"messageKey": "upload_text_track_failed", "message": "Text track upload failed.",'
                   ' "recordId": "baz", "returncode": "SUCCESS"}}', "application/json")
        with self.assertRaises(BBBException) as cm:
            self.bbb.put_recording_text_track("baz", "subtitles", "en-US", file_path=__file__)
        self.assertEqual(cm.exception.key, "upload_text_track_failed")

    def test_checksum_error(self):
        self.reply("<response><returncode>FAILED</returncode><messageKey>checksumError</messageKey>"
                   "<message>Checksums do not match</message></response>")
        with self.assertRaises(BBBException) as cm:
            self.bbb.get_meetings()
        self.assertEqual(cm.exception.key, BBBException.CHECKSUM_ERROR)

    def test_async_client_runs_calls_concurrently(self):
        bbb = AsyncBigBlueButton("bbb.example.com", SECRET)

        async def run():
            self.reply(MEETING_INFO)
            return await asyncio.gather(bbb.get_meeting_info("a"), bbb.get_meeting_info("b"),
                                        bbb.is_meeting_running("c"))

        info_a, info_b, running = asyncio.run(run())
        self.assertEqual(info_a.get_meetinginfo().get_meetingname(), "Anton G's Room")
        self.assertEqual(info_b.get_attendees()[0].get_fullname(), "Anton G")
        self.assertTrue(running.is_meeting_running())


if __name__ == "__main__":
    unittest.main()
