from .base import BaseResponse
from ..core.attendance import Attendance

class GetAttendanceResponse(BaseResponse):
    def get_attendance(self):
        attendances = []
        meetings = self.get_field("meetings")["meeting"]
        if type(meetings) != list:
            meetings = [meetings]
        for meeting in meetings:
            attendances.append(Attendance(xml=meeting))
        return attendances
