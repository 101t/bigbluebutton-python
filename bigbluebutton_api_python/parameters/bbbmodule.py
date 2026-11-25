import base64
import os
from xml.sax.saxutils import escape, quoteattr


class BBBModule:
    URL = "url"
    FILE = "file"
    base64s = "base64s"

    def __init__(self):
        self.__urls = []
        self.__files = []
        self.__base64s = []

    def add_slide(self, type, value, name=None):
        if type == self.URL:
            self.__urls.append(value)
        elif type == self.FILE:
            self.__files.append(value)
        elif type == self.base64s:
            self.__base64s.append([name, value])

    def has_slides(self):
        return bool(self.__urls or self.__files or self.__base64s)

    def to_xml(self):
        if not self.has_slides():
            return ""
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?><modules>" + self.__slides_to_xml() + "</modules>"

    def __slides_to_xml(self):
        xml = "<module name=\"presentation\">"
        for url in self.__urls:
            xml += "<document url=%s />" % quoteattr(url)

        for name, value in self.__base64s:
            xml += "<document name=%s>%s</document>" % (quoteattr(name or "document"), escape(value))

        for single_file in self.__files:
            if os.path.exists(single_file):
                with open(single_file, "rb") as f:
                    content = base64.b64encode(f.read()).decode("ascii")
                xml += "<document name=%s>%s</document>" % (quoteattr(os.path.basename(single_file)), content)

        return xml + "</module>"
