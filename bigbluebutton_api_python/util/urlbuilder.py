import hashlib
from urllib.parse import urlencode


class UrlBuilder:
    CHECKSUM_ALGORITHMS = ("sha1", "sha256", "sha384", "sha512")

    def __init__(self, bbbServerBaseUrl, securitySalt, checksum_algorithm="sha1"):
        if checksum_algorithm not in self.CHECKSUM_ALGORITHMS:
            raise ValueError("checksum_algorithm must be one of %s" % (self.CHECKSUM_ALGORITHMS,))
        if not bbbServerBaseUrl.startswith(("http://", "https://")):
            bbbServerBaseUrl = "https://" + bbbServerBaseUrl
        if not bbbServerBaseUrl.endswith("/bigbluebutton/api/"):
            host_end = bbbServerBaseUrl.find("/", 8)
            bbbServerBaseUrl = bbbServerBaseUrl[:host_end if host_end != -1 else None] + "/bigbluebutton/api/"

        self.securitySalt = securitySalt
        self.bbbServerBaseUrl = bbbServerBaseUrl
        self.checksum_algorithm = checksum_algorithm

    def buildUrl(self, api_call, params=None):
        query = urlencode({k: ("true" if v else "false") if isinstance(v, bool) else str(v)
                           for k, v in (params or {}).items()})
        checksum = hashlib.new(self.checksum_algorithm,
                               (api_call + query + self.securitySalt).encode("utf-8")).hexdigest()
        return self.bbbServerBaseUrl + api_call + "?" + (query + "&" if query else "") + "checksum=" + checksum
