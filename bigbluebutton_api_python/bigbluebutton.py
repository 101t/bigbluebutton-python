from .core import ApiMethod
from .responses import (
    ApiVersionResponse,
    BaseResponse,
    CreateMeetingResponse,
    DeleteRecordingsResponse,
    EndMeetingResponse,
    GetMeetingInfoResponse,
    GetMeetingsResponse,
    GetRecordingsResponse,
    IsMeetingRunningResponse,
    PublishRecordingsResponse,
    UpdateRecordingsResponse,
    GetAttendanceResponse
)
from .exception import BBBException
from .util import UrlBuilder
from .parameters import BBBModule
import json
import os
import uuid
from jxmlease import parse
from urllib.request import Request, urlopen
from urllib.parse import urlencode


def _with_meta(params, meta):
    params = dict(params or {})
    for key, val in (meta or {}).items():
        params["meta_" + key] = val
    return params


class BigBlueButton:
    MODERATOR = "MODERATOR"
    VIEWER = "VIEWER"

    def __init__(self, bbbServerBaseUrl, securitySalt, checksum_algorithm="sha1", timeout=10):
        self.__urlBuilder = UrlBuilder(bbbServerBaseUrl, securitySalt, checksum_algorithm)
        self.timeout = timeout

    def get_api_version(self):
        response = self.__send_api_request(ApiMethod.VERSION)
        return ApiVersionResponse(response)

    def create_meeting(self, meeting_id, params=None, meta=None, slides=None):
        params = _with_meta(params, meta)
        params["meetingID"] = meeting_id
        params.setdefault("name", meeting_id)  # required since BBB 2.4
        if isinstance(slides, BBBModule) and slides.has_slides():
            response = self.__send_api_request(ApiMethod.CREATE, params, slides.to_xml())
        else:
            response = self.__send_api_request(ApiMethod.CREATE, params)
        return CreateMeetingResponse(response)

    def get_join_meeting_url(self, full_name, meeting_id, password=None, params=None, role=None):
        """Build a join URL. Pass role=BigBlueButton.MODERATOR/VIEWER (BBB >= 2.4);
        password is deprecated but still accepted."""
        if role is None and password is None:
            raise ValueError("either role or password is required")
        params = dict(params or {})
        params["fullName"] = full_name
        params["meetingID"] = meeting_id
        if role is not None:
            params["role"] = role
        if password is not None:
            params["password"] = password
        return self.__urlBuilder.buildUrl(ApiMethod.JOIN, params)

    def is_meeting_running(self, meeting_id):
        params = {"meetingID": meeting_id}
        response = self.__send_api_request(ApiMethod.IS_MEETING_RUNNING, params)
        return IsMeetingRunningResponse(response)

    def end_meeting(self, meeting_id, password=None):
        params = {"meetingID": meeting_id}
        if password is not None:
            params["password"] = password
        response = self.__send_api_request(ApiMethod.END, params)
        return EndMeetingResponse(response)

    def get_meeting_info(self, meeting_id):
        params = {"meetingID": meeting_id}
        response = self.__send_api_request(ApiMethod.GET_MEETING_INFO, params)
        return GetMeetingInfoResponse(response)

    def get_meetings(self):
        response = self.__send_api_request(ApiMethod.GET_MEETINGS)
        return GetMeetingsResponse(response)

    def insert_document(self, meeting_id, slides):
        """Upload presentations into a running meeting. slides is a BBBModule."""
        response = self.__send_api_request(ApiMethod.INSERT_DOCUMENT, {"meetingID": meeting_id}, slides.to_xml())
        return BaseResponse(response)

    def send_chat_message(self, meeting_id, message, user_name=None):
        """Post a message to the public chat (BBB >= 3.0)."""
        params = {"meetingID": meeting_id, "message": message}
        if user_name is not None:
            params["userName"] = user_name
        response = self.__send_api_request(ApiMethod.SEND_CHAT_MESSAGE, params)
        return BaseResponse(response)

    def get_recordings(self, meeting_id=None, params=None):
        params = dict(params or {})
        if meeting_id is not None:
            params["meetingID"] = meeting_id
        response = self.__send_api_request(ApiMethod.GET_RECORDINGS, params)
        return GetRecordingsResponse(response)

    def publish_recordings(self, recording_id, publish=True):
        params = {"recordID": recording_id, "publish": "true" if publish else "false"}
        response = self.__send_api_request(ApiMethod.PUBLISH_RECORDINGS, params)
        return PublishRecordingsResponse(response)

    def delete_recordings(self, recording_id):
        params = {"recordID": recording_id}
        response = self.__send_api_request(ApiMethod.DELETE_RECORDINGS, params)
        return DeleteRecordingsResponse(response)

    def update_recordings(self, recording_id, meta=None):
        params = _with_meta({"recordID": recording_id}, meta)
        response = self.__send_api_request(ApiMethod.UPDATE_RECORDINGS, params)
        return UpdateRecordingsResponse(response)

    def get_recording_text_tracks(self, recording_id):
        response = self.__send_api_request(ApiMethod.GET_RECORDING_TEXT_TRACKS, {"recordID": recording_id})
        return BaseResponse(response)

    def put_recording_text_track(self, recording_id, kind, lang, label=None, file_path=None):
        """Upload a WebVTT/SRT caption file. Omitting file_path deletes the track."""
        params = {"recordID": recording_id, "kind": kind, "lang": lang}
        if label is not None:
            params["label"] = label
        url = self.__urlBuilder.buildUrl(ApiMethod.PUT_RECORDING_TEXT_TRACK, params)
        boundary = uuid.uuid4().hex
        body = b""
        if file_path is not None:
            with open(file_path, "rb") as f:
                body = (("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
                         "Content-Type: application/octet-stream\r\n\r\n") % (boundary, os.path.basename(file_path))
                        ).encode() + f.read() + b"\r\n"
        body += ("--%s--\r\n" % boundary).encode()
        request = Request(url, data=body, headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
        raw = self.__check(self._parse_response(urlopen(request, timeout=self.timeout)))
        if raw.get("messageKey") == "upload_text_track_failed":  # BBB reports this failure with returncode SUCCESS
            raise BBBException(raw["messageKey"], raw.get("message"))
        return BaseResponse(raw)

    def get_attendance(self, meeting_id, meta=None):
        params = _with_meta({"meetingID": meeting_id}, meta)
        response = self.__send_api_request(ApiMethod.GET_ATTENDANCE, params)
        return GetAttendanceResponse(response)

    def _parse_response(self, response):
        # parse response to the correct form
        content_type = response.getheader('Content-Type') or ""
        response = response.read()
        if content_type.startswith("application/json"):
            return json.loads(response)["response"]
        try:
            return parse(response)["response"]
        except Exception as e:
            raise BBBException(BBBException.XML_SYNTAX_ERROR, e)

    @staticmethod
    def __check(raw):
        if isinstance(raw, dict) and raw.get("returncode") == "FAILED":
            raise BBBException(raw.get("messageKey"), raw.get("message"))
        return raw

    def __send_api_request(self, api_call, params=None, data=None):
        url = self.__urlBuilder.buildUrl(api_call, params)

        # if data is none, then we send a GET request, if not, then we send a POST request
        if data is None:
            response = urlopen(url, timeout=self.timeout)
        elif isinstance(data, str):
            request = Request(url, data=data.encode("utf-8"), headers={'Content-Type': 'application/xml'})
            response = urlopen(request, timeout=self.timeout)
        else:
            response = urlopen(url, timeout=self.timeout, data=urlencode(data).encode())

        return self.__check(self._parse_response(response))
