# -*- coding: utf-8 -*-
"""
interpret smc script

main function:
- run_script
"""
from __future__ import print_function, unicode_literals

import os
import logging
import sys

# from mako.template import Template
from mako.lookup import TemplateLookup

# import yaml
# import json

from lxml import etree
import etconfig

from smcscript.utils import print_err, print_values, print_fmt
from smcscript.api import id_mapper
from smcscript.exceptions import SMCOperationFailure, ResolveError


# pylint: disable=invalid-name
logger = logging.getLogger(__name__)


class RunScriptError(Exception):
    """raise when the script contains an invalid operation (other than
    resource, delete, login...)
    """
    pass

def _get_target_hname(elt):
    """
    elt is sthg like:

    resource "xxx" {
        target="#yyy"
        some_elt {...}
    }

    return the concatenated "#yyy/xxx" or uses the tag of 'some_elt'

    """
    cmd_name = elt.get("name") or elt.text
    target = elt.get("target")

    if cmd_name is not None and target is not None:
        target = target + "/" + cmd_name
    elif cmd_name is not None:
        target = cmd_name
    else:
        # use the tag of the contained element
        assert elt is not None
        target = elt[0].tag

    return target


def do_login(smc_client, login_elt, print_only=False):
    """
    login from the script

    :param SMCClient smc_client: client to send requests to smc

    """
#todo
    raise Exception("login not implemented")

def do_logout(smc_client, logout_elt, print_only=False):
    """
    logout from the script

    :param SMCClient smc_client: client to send requests to smc

    """
#todo
    raise Exception("logout not implemented")



def do_update_elt(smc_client, target_hname, update_elt, print_only=False):
    """update a resource element in the smc

    :param SMCClient smc_client: client to send requests to smc
    :param etree.Element cmd_elt: element tree, example:

     update "#single_fw/myfw1" {
        add "//domain_server_addresses" {
            domain_server_address { value=8.8.4.4 rank=1.0 }
        }
    }

    :returns: None
    """

    #todo err
    smc_elt = smc_client.get(target_hname)

    for operation in update_elt:

        if operation.tag == "set":
            xpath_expr = operation.text
            smc_elt.merge(xpath_expr, operation)

        elif operation.tag == "del":
            xpath_expr = operation.text
            smc_elt.remove(xpath_expr)

        elif operation.tag == "add":
            xpath_expr = operation.text
            smc_elt.add(xpath_expr, *list(operation))
        else:
            print_err("invalid update {}", operation.tag)
            return

    if print_only:
        smc_elt.apply_changes()
        print(etconfig.dumps(smc_elt.data).encode('utf8'))
        return

    smc_client.update(smc_elt)


def do_execute(smc_client, target_hname, cmd_elt, print_only=False):
    """execute a command on a resource element in the smc

    :param SMCClient smc_client: client to send requests to smc
    :param etree.Element cmd_elt: element tree, example:
     eg
     command "add_route" {
        target="single_fw/myfw1"
        params.gateway "192.168.100.1";
        params.network "10.10.0.0/24";
    }

    :returns: None
    """
    # target_hname = _get_target_hname(cmd_elt)

    params = {}
    for param in cmd_elt.findall("params/*"):
        params[param.tag] = param.text

    for param in cmd_elt.findall("params"):
        for key, value in param.attrib.items():
            params[key] = value

    if print_only:
        print_values("post", target_hname, params=params)
        return

    resp = smc_client.execute(target_hname, **params)
    out = cmd_elt.get("out")
    if out:
        with open(out, 'w+') as the_file:
            the_file.write(resp)



# pylint: disable=unused-argument
def do_delete_elt(smc_client, target_hname, dlt_elt, print_only=False):
    """delete a resource element in the smc

    :param SMCClient smc_client: client to send requests to smc
    :param etree.Element dlt_elt: element tree, example:
     eg
          delete "#single_fw/fw1";

    :raises ResolveError:  resource to delete not found
    :raises SMCOperationFailure:  error reported by the smc

    :returns: None
    """
    try:
        smc_elt = smc_client.get(target_hname)
        smc_client.delete(smc_elt)
    except (ResolveError, SMCOperationFailure) as exc:
        logger.warn("Deletion of %s failed: %s", target_hname, exc)
        raise exc
    else:
        logger.info("Deletion of %s success", target_hname)


def do_create_elt(smc_client, target_hname, crte_elt, print_only=False):
    """create a resource element in the smc

    :param SMCClient smc_client: client to send requests to smc
    :param etree.Element crte_elt: element tree, represents a creation, example:

    resource {
       host "myhost12" {
          ipv6_address = fd12::11
       }
    }
    :param bool print_only: if true prints the request that would be sent

    :returns: None

    """
    # hname = _get_target_hname(crte_elt)
    elt = crte_elt[0]
    smc_client.create(elt, target_hname, print_only)


def preprocess_config_file(filename, variables=None):
    """
    preprocess the config file using mako template engine

    :param str filename: filename to preprocess using mako template engine
    :param dict user_variables: dict of name/value used as variables

    :returns: a string containing the preprocessed file
    :rtype: str


    :raises IOError: if filename could not be read
    :raises TemplateLookupException: failed to include a file
    :raises NameError: if a variable cannot be resolved
    :raises SyntaxException: syntax error during preprocessing

    """
    # improvement: let the user use its own template engine


    # todo error
    variables = variables or {}

    logging.debug("preprocessing '%s'", filename)


    lookup_dir = os.path.dirname(filename)
    mylookup = TemplateLookup(directories=[lookup_dir],
                              output_encoding='utf-8',
                              strict_undefined=True)

    tmpl = mylookup.get_template(os.path.basename(filename))
    rendered = tmpl.render(**variables)
    return rendered



def load_config_file(filename, variables=None):
    """read config file in xml/conf (todo yaml and json)

    :param str filename: filename to load
    :param dict user_variables: dict of name/value used as variables
    for mako engine

    :raises IOError: if filename could not be read
    :raises TemplateLookupException: failed to include a file
    :raises NameError: if a variable cannot be resolved
    :raises SyntaxException: syntax error during preprocessing
    :raises ElementConfError: failed to parse the filename (after processing)

    :returns: an xml tree representing the config file
    :rtype: etree.Element
    """

    variables = variables or {}

    logging.debug("load_config_file '%s'", filename)

    rendered = preprocess_config_file(filename, variables)


    if filename.endswith(".xml"):
        xml = etree.fromstring(str(rendered))
        conf = xml.getroot()

    elif filename.endswith(".json"):
        print("todo json...")
        sys.exit(1)
    elif filename.endswith(".yaml"):
        # yaml_data = yaml.load(rendered)
        # print(yaml_data)
        print("todo yaml...")
        sys.exit(1)
    else:
        conf = etconfig.loads(
            rendered, single_root_node=False, id_mapper=id_mapper)
    return conf


def _get_resource_name_to_delete(elt):
    name = elt[0].get("name")
    target_hname = _get_target_hname(elt) +"/" + name
    return target_hname


def _delete_all_resources(smc_client, resources):
    """
    iterate over a list of resources and delete them

    :param list of Element resources: list of resource to delete

    :returns: list of Element resources that could not be deleted
    :rtype: list
    """
    failed = []
    for elt in resources:
        target_hname = _get_resource_name_to_delete(elt)
        # print_values(target_hname=target_hname)
        try:
            do_delete_elt(smc_client, target_hname, elt)
            print_fmt("- delete {} successful", target_hname)
        except (ResolveError, SMCOperationFailure) as exc:
            failed.append(elt)
    return failed

def delete_all_resources(smc_client, conf):
    """
    iterate over all resources in the config file and try to delete them.
    Retries till there are failed resources and some resources were deleted
    in the previous iteration, to solve dependencies.
    """
    resources = conf.xpath("resource")

    while resources:
        failed = _delete_all_resources(smc_client, resources)
        num_resources_remaining = len(failed)
        if  num_resources_remaining == len(resources):
            print_fmt("{} resources could not be deleted", num_resources_remaining)
            for elt in failed:
                target_hname = _get_resource_name_to_delete(elt)
                print_fmt(" - {}", target_hname)
            return
        resources = failed

# pylint: disable=too-many-locals, too-many-arguments
def run_script(smc_client, filename, print_only=False,
               preprocess_only=False, user_variables=None,
               ignore_errors=False, delete_mode=False, cleanup_mode=False):
    """execute a script

    :param SMCClient smc_client: client to send requests to smc
    :param str filename: name of the file containing the script
    :param bool print_only: does not execute the script. only print
    :param bool preprocess_only: show the script after the template preprocessing
    :param dict user_variables: dict of name/value used as variables for
    template preprocessing

    :returns: None

    :raises IOError: if filename could not be read
    :raises TemplateLookupException: failed to include a file
    :raises NameError: if a variable cannot be resolved
    :raises SyntaxException: syntax error during preprocessing
    :raises ElementConfError: failed to parse the filename (after processing)
    :raises InvalidSessionError: not logged in or session expired
    :raises SMCOperationFailure: is smc server responds with status_code error

    """

    variables = {}
    lookup_dir = os.path.dirname(os.path.abspath(filename))
    var_config_file_name = lookup_dir + "/variables.cnf"
    logger.debug("var_config_file_name=%s", var_config_file_name)
    if os.path.isfile(var_config_file_name):
        var_elts = load_config_file(var_config_file_name)
        for var_elt in var_elts:
            name = var_elt.get("name")
            value = var_elt.get("default")
            variables[name] = value

    if user_variables:
        variables.update(user_variables)

    if preprocess_only:
        rendered = preprocess_config_file(filename, variables)
        print (rendered)
        return

    conf = load_config_file(filename, variables)

    if delete_mode or cleanup_mode:
        print ("Cleaning up...")
        delete_all_resources(smc_client, conf)
        if delete_mode:
            return

    operations = dict(
        login=do_login,
        logout=do_logout,
        resource=do_create_elt,
        delete=do_delete_elt,
        update=do_update_elt,
        command=do_execute)

    print ("Applying config...")

    for elt in conf:
        operation = elt.tag
        target_hname = _get_target_hname(elt)

        if operation == 'resource':
            name = elt[0].attrib.get("name", "")
            op_text = "{} {}/{}...".format(operation, target_hname, name)
        else:
            op_text = "{} {}...".format(operation, target_hname)

        logging.info("script command: %s", op_text)
        print_fmt("- {}", op_text)
        if operation not in operations:
            raise RunScriptError("invalid operation: "+ operation)
        fun = operations.get(operation)

        try:
            fun(smc_client, target_hname, elt, print_only)
        except (SMCOperationFailure, ResolveError) as exc:
            if ignore_errors:
                print_err(" => Ignoring error: {}", unicode(exc))
                continue
            raise SMCOperationFailure(unicode(exc))
    return
