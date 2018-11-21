# -*- coding: utf-8 -*-
"""low level api. Keeps together the Session api and the requests api
and deals with session save/restore/autologin

"""
from __future__ import print_function, unicode_literals
import logging

from lxml import etree

from smcscript.session import Session
from smcscript.exceptions import InvalidSessionError, SMCOperationFailure, UnsupportedEntryPoint
from smcscript.utils import load_session, save_session

# pylint: disable=invalid-name
logger = logging.getLogger(__name__)



class SMCRestApiClient(object):
    """
    rest client: wrapper of requests using smc session
    """
    def __init__(self, smc_session=None, auto_login=False, session_file_path=None):
        """constructor

        :param smcscript.session.Session smc_session: session to access the smc rest api
        :param bool auto_login: attempt to auto login using ~/.smcrc

        """
        self._smc_session = smc_session
        self._auto_login_enabled = auto_login
        self._auto_login_attempted = False
        self._session_file_path = session_file_path


    @property
    def smc_session(self):
        """return an instance of smcscript.session.Session

        :returns: return the session or None if no session
        :rtype: smcscript.session.Session
        """
        if self._smc_session:
            return self._smc_session

        # no session, let see if we can restore one from the session_file_path
        if self._session_file_path:
            self._smc_session = load_session(self._session_file_path)
            if self._smc_session:
                return self._smc_session

        # still no session, let see if we can make one by autologin
        if self._auto_login_enabled:
            self.auto_login()

        return self._smc_session

    def make_url(self, endpoint, path=None):
        """return the url for the given endpoint

        :param str endpoint: desired endpoint (e.g. single_fw). The
        list of endpoints can be obtained using 'smc-script list' or
        programmatically using smc_session.entry_points.get(endpoint)

        :param str path: path to append

        :returns: the url for the given endpoint or None on error
        :rtype: str

        e.g.

        http://192.168.100.7:8082/6.6/elements/single_fw


        """
        if not self.smc_session:
            return None

        try:
            url = self.smc_session.entry_points.get(endpoint)
        except UnsupportedEntryPoint as exc:
            logger.error("UnsupportedEntryPoint: %s", exc)
            return None

        if path:
            if path[0] == '/':
                url = url + path
            else:
                url = url + '/' + path

        # logger.debug("make_url %s: %s",
        #              endpoint+"/"+ path if path else endpoint, url)
        return url



    def auto_login(self):
        """
        attempt to auto login using ~/.smcrc
        on success, the session is saved to 'session_file_path'

        :returns: True on success
        :rtype: bool

        """
        logger.info("attempting to autologin")
        if self._auto_login_attempted:
            return False

        self._auto_login_attempted = True

        if not self._smc_session:
            self._smc_session = Session()
        try:
            self._smc_session.login()
            if self._session_file_path:
                save_session(self._smc_session, self._session_file_path)
        # pylint: disable=broad-except
        except Exception as exc:
            logger.error("auto login attempt failed: %s", unicode(exc))
            return False
        logger.info("autologin success")
        return True


    @staticmethod
    def _format_error(resp):
        """extract error message from http response

        :returns: (message, detail)
        :rtype: tuple

        """
        message = ""
        details = ""
        if not resp.headers:
            message = "Error {}".format(resp.status_code)
            return (message, details)

        content_type = resp.headers.get('content-type')
        if not content_type:
            message = "Error {}".format(resp.status_code)
            return (message, details)

        if content_type.startswith('application/json'):
            try:
                data = resp.json()
            except ValueError:
                message = "Error {}".format(resp.status_code)
            else:
                message = data.get('message', None)
                details = data.get('details', None)
                if isinstance(details, list):
                    details = " ".join(details)

        elif content_type.startswith('application/xml'):
            xml = etree.XML(str(resp.text))
            message=xml.get("message")
            details=xml.get("details")

        elif resp.text:
            message = resp.text
        else:
            message = "Error {}".format(resp.status_code)

        return (message, details)


    @staticmethod
    def _check_response(method, resp):
        """
        return True if response was successful, else raise SMCOperationFailure
        """
        method = method.upper()
        success_status = {
            'GET': (200, 204, 304),
            'POST': (200, 201, 202),
            'PUT': (200,),
            'DELETE': (200, 204)
        }

        status_code = resp.status_code
        if status_code in success_status[method]:
            return True

        (message, details) = SMCRestApiClient._format_error(resp)
        logger.error("HTTP response error: status=%s, message=%s, details=%s",
                     resp.status_code, message, details)
        if details:
            raise SMCOperationFailure("{} {}".format(message, details))
        else:
            raise SMCOperationFailure(message)

    # pylint: disable=too-many-arguments
    def request(self, method, url, params=None, data=None, headers=None,
                json=None, **kwargs):
        """enhancement of requests module
        - if 401, try to reinitiate a login and re-attempt the operation

        :raises SMCOperationFailure: if status_code is not 2xx or 3xx

        """
        res = None

        if url is None:
            raise ValueError("url is null")

        request_session = self.smc_session.session if self.smc_session else None

        if not request_session:
            if not self._auto_login_enabled:
                logger.error("not logged in")
                raise InvalidSessionError("not logged in")
            else:
                if not self.auto_login():
                    raise InvalidSessionError(
                        "Not logged in and " +
                        "Unable to autologin. Hint: check ~/.smcrc")

        logger.debug("url=%s", url)
        # pylint: disable=unused-variable
        for retry in (0, 1):
            res = request_session.request(method, url, params=params, data=data,
                                          headers=headers, json=json, **kwargs)

            if res.status_code == 401:
                # this was a login error. Let's try to login automatically
                # and retry
                logger.warning("request failed: session expired")
                if not self._auto_login_enabled:
                    raise InvalidSessionError("not logged in or session expired")
                elif not self.auto_login():
                    raise InvalidSessionError(
                        "Not logged in/session expired and " +
                        "unable to autologin. Hint: check ~/.smcrc")
                continue
            else:
                SMCRestApiClient._check_response(method, res)
                break


        return res

    def get(self, url, **kwargs):
        """see requests module """
        kwargs.setdefault('allow_redirects', True)
        return self.request('GET', url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """see requests module """
        return self.request('POST', url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        """see requests module """
        return self.request('PUT', url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """see requests module """
        return self.request('DELETE', url, **kwargs)
