# bigbluebutton-python

[![PyPI](https://img.shields.io/pypi/v/bigbluebutton-python)](https://pypi.org/project/bigbluebutton-python/)

Python client for the [BigBlueButton API](https://docs.bigbluebutton.org/development/api), covering the BigBlueButton 3.x endpoints.

## Installation

```shell
pip install bigbluebutton-python
```

The import name is `bigbluebutton_api_python`, so code written against the older package keeps working.

## Quick start

```python
from bigbluebutton_api_python import BigBlueButton

# The secret comes from `bbb-conf --secret`.
bbb = BigBlueButton("https://bbb.example.com/bigbluebutton/api/", "your-shared-secret")
# BBB >= 2.5 also accepts checksum_algorithm="sha256" (or sha384 / sha512).

print(bbb.get_api_version().get_version())

bbb.create_meeting("room-1", params={"name": "Daily standup", "record": True}, meta={"team": "core"})

moderator_url = bbb.get_join_meeting_url("Alice", "room-1", role=BigBlueButton.MODERATOR)
viewer_url = bbb.get_join_meeting_url("Bob", "room-1", role=BigBlueButton.VIEWER)

bbb.send_chat_message("room-1", "Welcome!")  # BBB >= 3.0
info = bbb.get_meeting_info("room-1").get_meetinginfo()
bbb.end_meeting("room-1")
```

### Presentations

```python
from bigbluebutton_api_python.parameters import BBBModule

slides = BBBModule()
slides.add_slide(BBBModule.URL, "https://example.com/deck.pdf")
slides.add_slide(BBBModule.FILE, "local/agenda.pdf")

bbb.create_meeting("room-1", slides=slides)  # preload slides when the meeting is created
bbb.insert_document("room-1", slides)        # add slides to a meeting that is already running
```

### Recordings

```python
for rec in bbb.get_recordings(meeting_id="room-1").get_recordings():
    print(rec.get_recordid(), rec.get_name())

bbb.publish_recordings("record-id", publish=False)
bbb.update_recordings("record-id", meta={"title": "Renamed"})
bbb.get_recording_text_tracks("record-id")
bbb.put_recording_text_track("record-id", kind="subtitles", lang="en_US", label="English", file_path="en.vtt")
bbb.delete_recordings("record-id")
```

A request that fails raises `bigbluebutton_api_python.exception.BBBException`. Its `.key` attribute holds the BBB `messageKey`.

## Supported endpoints

`create`, `join`, `end`, `isMeetingRunning`, `getMeetingInfo`, `getMeetings`, `insertDocument`, `sendChatMessage`, `getRecordings`, `publishRecordings`, `deleteRecordings`, `updateRecordings`, `getRecordingTextTracks`, `putRecordingTextTrack`, `getAttendance`.

## Upgrading from 0.0.x

- `setConfigXML` and `getDefaultConfigXML` are gone. BigBlueButton itself removed them in 2.4.
- Joining with `role=` is preferred over the deprecated `password`. `end_meeting` no longer needs a password.
- Python 3.9 or newer is required.

## Development

```shell
pip install -e .
python -m unittest discover -s tests
```

## Releasing

Pushing a `v*` tag runs the tests and publishes to PyPI through GitHub Actions ([Trusted Publishing](https://docs.pypi.org/trusted-publishers/)).

## License

LGPL-3.0-or-later
