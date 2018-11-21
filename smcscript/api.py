# -*- coding: utf-8 -*-
"""
high level api based on Element.
"""
from __future__ import print_function, unicode_literals
import logging

import etconfig
from etconfig import utils as et_utils
from lxml import etree
# pylint: disable=no-name-in-module
from lxml.builder import E

# from smcscript.session import Session
from smcscript.resolver import resolve_hname, resolve_elt_hnames
from smcscript.restapi import SMCRestApiClient
from smcscript.utils import print_fmt, print_err
from smcscript.exceptions import ResolveError, SMCOperationFailure

# pylint: disable=invalid-name
logger = logging.getLogger(__name__)


CREATE_PRINT_FMT = """\
Element {tag}/{name}:
--------------------------
{verb} {target_href}
{xml}"""



def id_mapper(elt, idlist):
    """
    convert the idlist to attribute "name"
    """
    # special case for 'update' element
    if (elt.tag == 'set' or elt.tag == 'add'):
        elt.text = idlist[-1]
    else:
        elt.set("name", idlist[-1])

def cnf_elt(text):
    """parses a textual representation (cnf) of an element (e.g. a
single_fw) and returns an etree Element

    """
    data = etconfig.loads(text, single_root_node=True, id_mapper=id_mapper)
    return data



def _stringify_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)

def _stringify_dict_values(d):
    return {key: _stringify_value(value) for (key, value) in d.items()}


class SMCElement(object):
    """
    represents the xml data of an element (e.g. a single_fw)
    """
    def __init__(self, data, hname=None, etag=None):
        """
        data is an etree Element
        """
        self.hname = hname or data.tag
        self.etag = etag
        self.data = data
        self.change_list = []


    def get(self, xpath_expr):
        """
        return the first item matching xpath_expr
        """
        if self.data is None:
            return None

        res = self.data.xpath(xpath_expr)
        if res and len(res) >= 1:
            return res[0]
        return None

    def get_all(self, xpath_expr):
        """
        return the items matching xpath_expr
        """
        if self.data is None:
            return None

        res = self.data.xpath(xpath_expr)
        return res

    def apply_changes(self):
        """
        apply the change_list to this object
        """
        # todo errors
        for change in self.change_list:
            change()

    def set_values(self, xpath_expr=None, **kwargs):
        """
        set the values of the etree element matching the xpath_expr
        """

        attrs = _stringify_dict_values(kwargs)
        el = E.update_node(**attrs)
        self.merge(xpath_expr, el)

    def merge(self, xpath_expr, update_elt):
        """
        merge the existing element at the xpath with the supplied element
        the tag of the supplied elt is ignored
        """
        elt = self.data

        def _merge_change():
            if xpath_expr:
                matching_nodes = elt.xpath(xpath_expr)
                if len(matching_nodes) != 1:
                    print_err("error set: {}, number of nodes match: {} "\
                              "(should be exactly 1)", xpath_expr,
                              len(matching_nodes))
                    return
                et_utils.elt_merge(update_elt, matching_nodes[0])
            else:
                et_utils.elt_merge(update_elt, elt)
        self.change_list.append(_merge_change)

    def remove(self, xpath_expr):
        """
        remove etree element node matching xpath_expr
        """
        elt = self.data
        def _remove_change():
            matching_nodes = elt.xpath(xpath_expr)

            if not matching_nodes:
                print_err("error deleting {}: element not found", xpath_expr)
                return

            if len(matching_nodes) != 1:
                print_err("error deleting {}, number of elements found: {} "\
                          "(should be exactly 1)", xpath_expr, len(matching_nodes))
                return
            matching_nodes[0].getparent().remove(matching_nodes[0])
        self.change_list.append(_remove_change)

    def add(self, xpath_expr, *elements):
        """
        add child
        """
        if xpath_expr is None:
            print_err("add: xpath expr is mandatory")
            return

        elt = self.data
        def _add_change():
            matching_nodes = elt.xpath(xpath_expr)
            if len(matching_nodes) != 1:
                print_err("error adding: {}, number of nodes match: {} "\
                          "(should be exactly 1)", xpath_expr, len(matching_nodes))
                return
            for elt_to_add in elements:
                matching_nodes[0].append(elt_to_add)
        self.change_list.append(_add_change)


    def add_after(self, xpath_expr, elt):
        """
        add after sibling
        """
        pass

    def add_before(self, xpath_expr, elt):
        """
        add before sibling
        """
        pass

    def __str__(self):
        res = etconfig.dumps(
            self.data, indent=0, indent_chars=" "*4, print_root=True)
        return res



class SMCClient(object):
    """
    high level api to access the smc rest api based on Element
    """

    def __init__(self, session_file_path=None):
        self._client = SMCRestApiClient(auto_login=True,
                                        session_file_path=session_file_path)

    @property
    def rest_client(self):
        return self._client

    @property
    def session(self):
        """return an instance of smcscript.session.Session"""
        return self._client.smc_session

    def login(self, **kwargs):
        """
        see session login
        """
        res = self.session.login(**kwargs)
        return res

    def logout(self):
        """
        see session logout
        """
        self.session.logout()


    def create(self, elt, hname=None, print_only=False):
        """send a POST request to the smc rest api to create an element

        :param etree.Element elt: represents the element data to
        create in xml e.g.  <single_fw>...</single_fw>

        :param str hname: hierarchical name that will result in the
        url endoint. It can be omitted if the hname is the same as the
        element tag. e.g. hname="#single_fw"

        :returns: None

        :raises ResolveError: fails to convert a hname to a url
        (either the target or an url in an attribute of the element)

        :raises SMCOperationFailure: if creation unsuccessful

        """
        if not hname:
            hname = elt.tag

        logger.debug("create resource hname=%s", hname)

        # ResolveError exception is propagated
        target_href = resolve_hname(self._client, hname)
        resolve_elt_hnames(self._client, elt, ignore_errors=print_only)

        xml = etree.tostring(elt, encoding='utf8', pretty_print=True)
        if print_only:
            print_fmt(CREATE_PRINT_FMT,
                      verb="POST",
                      target_href=target_href,
                      tag=elt.tag,
                      name=elt.get("name", "-"),
                      xml=xml)
            return

        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        resp = self._client.post(target_href, headers=headers, data=xml)
        logger.debug("status_code=%d", resp.status_code)
        logger.debug("text=%s", resp.text)


    def get(self, hname):
        """return an SMCElement corresponding to the given hname

        eg
        get("#single_fw/fw1")

        :returns: SMCElement with data containing the xml elements
        as etree Element and etag properly set or None on error
        :rtype: SMCElement


        """
        try:
            target_href = resolve_hname(self._client, hname)
        except ResolveError as err:
            raise err

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/xml'
        }
        res = self._client.get(target_href, headers=headers)

        # todo err
        text = res.text.encode('utf8')

        if not text:
            return None
        data = etree.fromstring(str(text))
        etag = res.headers.get("ETag")
        return SMCElement(data, hname, etag)


    def list(self, hname=None):
        """
        return a list of names below the given hname

        e.g.

        list("#single_fw")
        returns
        ["fw1", "fw2"]
        """
        res = []
        if not hname:
            res = [e.rel for e in iter(self.session.entry_points)]
        else:
            smc_element = self.get(hname)
            res = smc_element.data.xpath("/results_page/result/@name")

            if not res:
                res = smc_element.data.xpath("links/link/@rel")
        return res


    def delete(self, target):
        """delete an element. You need to pass the SMCElement, because
        deletion requires an etag
        """
        # todo error

        if isinstance(target, SMCElement):
            smc_element = target
        else:
            smc_element = self.get(target)

        target_href = resolve_hname(self._client, smc_element.hname)

        # todo refresh etags if object has changed
        resp = self._client.delete(target_href, headers={
            'If-Match': smc_element.etag
        })
        logger.debug("status_code=%d", resp.status_code)
        logger.debug("text=%s", resp.text)


    def update(self, smc_element, print_only=False):
        """
        apply the change list of an smc element and send a rest call
        to update the object in the smc.

        :raises SMCOperationFailure: if update unsuccessful

        """
        # todo refresh etags if object has changed
        # todo exc

        headers = {'If-Match': smc_element.etag, 'Content-Type': 'application/xml'}

        target_href = resolve_hname(self._client, smc_element.hname)

        # todo error
        smc_element.apply_changes()
        resolve_elt_hnames(self._client, smc_element.data)

        xml = etree.tostring(smc_element.data, pretty_print=True)

        if print_only:
            elt = smc_element.data
            print_fmt(CREATE_PRINT_FMT,
                      verb="PUT",
                      target_href=target_href,
                      tag=elt.tag,
                      name=elt.get("name", "-"),
                      xml=xml)
            return

        try:
            resp = self._client.put(target_href, headers=headers, data=xml)
        except SMCOperationFailure as exc:
            logger.error("Failed to update '%s'", unicode(exc) )
            raise exc
        smc_element.change_list = []

    def execute(self, target, operation=None, **kwargs):
        """
        target is either an hname or an instance of SMCElement
        """
        hname = target.hname  if isinstance(target, SMCElement) else target
        if operation:
            hname = hname + "/" + operation

        target_href = resolve_hname(self._client, hname)

        headers = {
            'Accept': 'application/json', 'Content-Type': 'application/json'
        }

        if isinstance(target, SMCElement):
            headers['If-Match'] = target.etag

        # exceptions propagated: eg SMCOperationFailure
        resp = self._client.post(target_href, headers=headers, params=kwargs)
        return resp.text
