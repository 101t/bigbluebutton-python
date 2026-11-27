import asyncio
import functools

from .bigbluebutton import BigBlueButton


class AsyncBigBlueButton(BigBlueButton):
    """Same API as BigBlueButton, but every network call is awaitable.

    get_join_meeting_url only builds a URL, so it stays synchronous.
    """


def _awaitable(method):
    @functools.wraps(method)
    async def wrapper(*args, **kwargs):
        # shortcut: urllib blocks, so each call takes a worker thread; switch to an async HTTP client if you need thousands of concurrent calls
        return await asyncio.to_thread(method, *args, **kwargs)
    return wrapper


for _name in ("get_api_version", "create_meeting", "is_meeting_running", "end_meeting", "get_meeting_info",
              "get_meetings", "insert_document", "send_chat_message", "get_recordings", "publish_recordings",
              "delete_recordings", "update_recordings", "get_recording_text_tracks", "put_recording_text_track",
              "get_attendance"):
    setattr(AsyncBigBlueButton, _name, _awaitable(getattr(BigBlueButton, _name)))
