import httplib
import urllib


class Connection:
    """Kraken.com connection handler.
    Public methods:
    close
    """


    def __init__(self, uri = 'api.kraken.com', timeout = 30):
        """ Create an object for reusable connections.

        Arguments:
        uri     -- URI to connect to (default: 'https://api.kraken.com')
        timeout -- blocking operations' timeout in seconds (default: 30)
        """
        self.headers = {
            'User-Agent': 'krakenex/0.0.5 (+https://github.com/veox/python2-krakenex)'
        }

        self.conn = httplib.HTTPSConnection(uri, timeout = timeout)


    def close(self):
        """ Close the connection.
        No arguments.
        """
        self.conn.close()


    def _request(self, url, req = {}, headers = {}):
        """ Send POST request to API server.

        url     -- Fully-qualified URL with all necessary urlencoded
                   information (string, no default)
        req     -- additional API request parameters (default: {})
        headers -- additional HTTPS headers, such as API-Key and API-Sign
                   (default: {})
        """
        data = urllib.urlencode(req)
        headers.update(self.headers)

        self.conn.request("POST", url, data, headers)
        response = self.conn.getresponse()

        return response.read()
