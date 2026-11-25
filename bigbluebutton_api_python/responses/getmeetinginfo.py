from .base import BaseResponse
from ..core.meetinginfo import MeetingInfo
from ..core.attendee import Attendee


class GetMeetingInfoResponse(BaseResponse):
    def get_meetinginfo(self):
        return MeetingInfo(xml=self.rawXml)

    def get_attendees(self):
        attendees = []

        field = self.get_field("attendees")
        if field == "":
            return []

        obj = field["attendee"]
        if isinstance(obj, list):
            for attendeeXml in obj:
                attendees.append(Attendee(xml=attendeeXml))
        else:
            attendees.append(Attendee(xml=obj))

        return attendees
