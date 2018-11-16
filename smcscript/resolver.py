# -*- coding: utf-8 -*-
"""
translate hname(symbolic names) into proper urls

main functions:
- resolve_elt_hnames
- resolve_hname
"""
from __future__ import print_function, unicode_literals

import sys
import re
import logging
from urlparse import urlparse

from lxml import etree

from smcscript.exceptions import ResolveError
from smcscript.utils import print_values, print_fmt


# pylint: disable=invalid-name
logger = logging.getLogger(__name__)




#----------------------------------------------------------------------
# transform href into hname
#----------------------------------------------------------------------

def split_hname(hname):
    """split a hierarchical name (hname) into parts.

    double '/' is used to escape the '/'.
    and is transformed into a into single '/'

    e.g.
        hname = "network/network-fd02:://64"
        => ["network", "network-fd02::/64"]

    :param str hname: hierarchical name
    :returns: a list with the splitted parts of the hname
    :rtype: list
    """
    lst = []
    cat = None
    for part in re.split(r"/(?=[^/])", hname):
        if cat:
            part = cat + part
            cat = None
        if part[-1] == '/':
            cat = part
        else:
            lst.append(part)
    return lst


def get_index(part):
    """
    check if the part is, e.g [123]
    return 123 or None
    """
    index = None
    match = re.match(r'\[(\d+)\]', part)
    if match:
        index = int(match.group(1))
    return index

# def get_element_url_by_name(rest_clt, elt, name):
#     """
#     get the url of an element by its element type and name,

#     e.g.
#     get_element_url_by_name(rest_clt, "single_fw", "fw1")

#     => http://192.168.100.7:8082/6.6/elements/single_fw/1429

#     return None if not found
#     """

#     index = get_index(name)

#     if index is not None:
#         url = rest_clt.make_url("elements", elt)
#         resp = rest_clt.get(url, headers={'Accept': 'application/json'})

#     else:
#         index = 0
#         url = rest_clt.make_url("elements")
#         resp = rest_clt.get(
#             url, headers={'Accept':'application/json'},
#             params={
#                 'exact_match':True,
#                 'filter': name,
#                 'filter_context' : elt
#             })

#     if resp.status_code not in (200, 204, 304):
#         return None

#     if not resp.text:
#         return None

#     json_resp = resp.json()
#     if not "result" in json_resp:
#         return None

#     result = json_resp.get("result")
#     if not result:
#         return None

#     href = result[index].get("href")
#     return href

# def get_element_links(rest_clt, element_url):
#     """
#     return the json array containing the list of links of an element

#     e.g.
#     get_element_links("http://192.168.100.7:8082/6.6/elements/single_fw/1462")

#     => [
#          {
#             "href": "http://192.168.100.7:8082/6.6/elements/single_fw/1462/firewall_node/1463",
#             "rel": "self",
#             "type": "firewall_node"
#         }, ...
#     """
#     res = rest_clt.get(element_url, headers={'Accept': 'application/json'})
#     json_res = res.json()
#     links = json_res.get("link")
#     return links


# def get_link_url_by_name(rest_clt, element_url, name):
#     """
#     return the url of a linked element
#     e.g.
#     get_link_url_by_name(
#         "http://192.168.100.7:8082/6.6/elements/single_fw/1429",
#         "routing"
#     )

#     => http://192.168.100.7:8082/6.6/elements/single_fw/1429/routing/258

#     """
#     links = get_element_links(rest_clt, element_url)
#     for lk in links:
#         if lk.get("rel") == name:
#             return lk.get("href")
#     return None


# def get_sub_element_url_by_name(rest_clt, link_url, sub_name):
#     """
#     todo doc
#     """
#     resp = rest_clt.get(link_url)
#     json_resp = resp.json()
#     # print_values("res:", resp.text, sub_name)

#     if not "result" in json_resp:
#         return None

#     match = re.match(r'\[(\d+)\]', sub_name)
#     if match:
#         index = int(match.group(1))
#         return json_resp.get("result")[index]["href"]
#     else:
#         for r in json_resp.get("result"):
#             if r["name"] == sub_name:
#                 return r["href"]
#     return None

def _get_href_from_xpath(data, part, xpath_expr, attr_name):
    results = data.xpath(xpath_expr)
    index = get_index(part)
    if index is not None:
        if index < len(results):
            return results[index].get("href")
    for r in results:
        if r.get(attr_name) == part:
            result = r.get("href")
            return result
    return None

def get_href_from_results(data, part):
    """
    get href from xml result
    """
    return _get_href_from_xpath(data, part, "/results_page/result", "name")

def get_href_from_links(data, part):
    """
    get href from xml links
    """
    return _get_href_from_xpath(data, part, "links/link", "rel")


def resolve_hname(rest_clt, hname):
    """
    return the url corresponding to the hierarchical name (hname)

     the hname:
     - (optionally) starts with '#'
     - if relative hname, means /elements/
     eg
         #fw_policy/fws30policy/fw_ipv6_nat_rules/Rule @2097190.1
         #log_server/LogServer 192.168.100.7


    :param str hname: hierarchical name to be converted to an url
    :param SMCRestApiClient rest_clt: client to send smc api requests

    :returns: returns the url corresponding to the hname
    :rtype: str

    :raises ResolveError: failed to resolve the hname
    :raises SMCOperationFailure: the smc report an error

    """

    # hname = "<elt>/<name>/<link>/<sub_name>"

    # if 2 parts, get by element and name
    # if 3 parts, get by element and name, then get link 'rel'
    # if 4 parts, get by element and name, then get link 'rel', then sub_name

    logger.debug("resolve %s", hname)

    if hname.startswith("http"):
        return hname

    if hname[0] == '#':
        hname = hname[1:]

    # todo absolute hname not supported, for now only /elements resolved
    # (not /system, but is it needed ?)
    hname_parts = split_hname(hname)

    # element_url = None
    # link_url = None
    # sub_element_url = None
    result_url = None

    if len(hname_parts) >= 1:
        elt = hname_parts[0]
        result_url = rest_clt.make_url(elt)

    # if len(hname_parts) >= 2:
    #     name = hname_parts[1]

    #     element_url = get_element_url_by_name(rest_clt, elt, name)
    #     if element_url is None:
    #         raise ResolveError("Cannot resolve hname '{}/{}'".format(elt, name))
    #     result_url = element_url

    for part in hname_parts[1:]:
        # exceptions of SMCRestApiClient are propagated
        resp = rest_clt.get(result_url, headers={'Accept': 'application/xml'})
        # print(resp.text)
        data = etree.fromstring(str(resp.text))
        result_url = get_href_from_links(data, part)
        if not result_url:
            result_url = get_href_from_results(data, part)
        if not result_url:
            raise ResolveError("Cannot resolve hname part '{}'".format(part))

    if result_url is None:
        raise ResolveError("Failed to get url for {}".format(hname))

    logger.debug("resolved: target_href=%s", result_url)
    return result_url


def resolve_elt_hnames(rest_clt, elt, ignore_errors=False):
    """resolve all href of an element.

    iterate recursively over an element and resolve all the hname
    contained either in the text of the element or in the attribute
    value.

    :param SMCRestApiClient rest_clt: client to send smc api requests
    :param etree.Element elt: xml data representing the smc element
    :param bool ignore_errors: if true does not raise an exception if
    an hname cannot be resolved

    :raises ResolveError: failed to resolve an hname

    """
    for e in elt.iter():
        if e.text and e.text[0] == '#':
            try:
                url = resolve_hname(rest_clt, e.text)
                e.text = url
            except ResolveError as exc:
                if not ignore_errors:
                    raise exc

        for k in e.attrib:
            v = e.attrib[k]
            if v and v[0] == '#':
                try:
                    url = resolve_hname(rest_clt, v)
                    e.attrib[k] = url
                except ResolveError as exc:
                    if not ignore_errors:
                        raise exc
