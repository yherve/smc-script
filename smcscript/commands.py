# -*- coding: utf-8 -*-
"""
CLI functions
"""
from __future__ import print_function, unicode_literals

import time
import logging

import os
import sys
import yaml
import subprocess
import tempfile

from lxml import etree
import etconfig

from argh.decorators import arg, named
from mako.template import Template
from mako.lookup import TemplateLookup
from mako.exceptions import TemplateLookupException, SyntaxException

from smcscript.exceptions import SMCConnectionError, InvalidSessionError, \
    ResolveError, SMCOperationFailure, CommandError
from smcscript.session import Session as SMCSession
from smcscript.api import SMCClient
from smcscript.script import run_script, RunScriptError
from smcscript.resolver import resolve_hname

from smcscript.utils import get_session_file_path, print_err, print_fmt, save_session, load_session


# pylint: disable=invalid-name
logger = logging.getLogger(__name__)


#----------------------------------------------------------------------
# commands
#----------------------------------------------------------------------

@arg("server", help="address or name of the SMC to log to",
     default=None, nargs='?')
@arg("-k", "--api-key", dest="api_key", required=False,
     help="api key of the SMC rest API")
@arg("-s", "--secure", dest="secure", action="store_const",
     const=False, help="Use HTTPS to connect")
@arg("-c", "--cacert", dest="ca_cert",
     help="path of the CA certificate to verify the connection")
@arg("-p", "--port", default=8082, help="TCP port of the SMC rest API")
@arg("-v", "--version", help="API version to use (e.g. 6.4). If not specified, the highest version is selected")
@arg("-f", "--file", dest="smcrc",
     help="provide login info in given file (same format as ~/.smcrc)")
@arg("-a", "--auto", help="login using ~/.smcrc)")
@named("login")
def cmd_login(server, secure=False, port=None, api_key=None,
              version=None, ca_cert=None, smcrc=None, auto=False):
    """
    login to the smc (rest api)

    If a file is specified using '-f' or --file, it must have the following format:

    [smc]
    smc_address=192.168.100.7
    smc_apikey=xxxx
    api_version=6.4
    smc_port=8082
    smc_ssl=False
    verify_ssl=False
    ssl_cert_file=''

    """
    #todo tls

    if not server and not smcrc and not auto:
        raise CommandError("Must have either --file or <server> or --auto")

    if int(server is not None)+int(smcrc is not None)+int(auto) > 1:
        raise CommandError("Cannot have both <server> and/or --file and/or --auto")

    if server and not api_key:
        raise CommandError("missing --api-key")

    proto = "https" if secure else "http"
    url = "{proto}://{host}:{port}".format(host=server, port=port, proto=proto) \
                                                 if server else None

    verify = ca_cert or False
    sess = SMCSession()

    try:
        sess.login(url=url, api_key=api_key, verify=verify,
                   api_version = version,
                   alt_filepath=smcrc)
        #todo save to another place (env var)
        if not save_session(sess):
            print_err("Failed to save session")
        return "login successful"
    except SMCConnectionError as conn_error:
        logger.exception(conn_error)
        raise CommandError(
            "connection to '{}:{}' failed\n({})".format(server, port, conn_error))


@named("logout")
def cmd_logout():
    """
    logout from the smc
    """
    session_file_path = get_session_file_path()
    if os.path.isfile(session_file_path):
        sess = load_session(session_file_path)
        sess.logout()
        os.remove(session_file_path)

@named("push")
@arg("-p", "--policy", dest="policy", required=True)
def cmd_push(hname, policy=None):
    session_file_path = get_session_file_path()
    smc_client = SMCClient(session_file_path)

    try:
        res = smc_client.execute(hname, operation="upload", params={'filter': policy})
        xml = etree.XML(str(res))
        follower = xml.findtext("follower")
        print(follower)
        while True:
            res2= smc_client.get(follower)
            print(res2)
            print(time.sleep(2))

    except Exception as exc:
        raise CommandError(exc)

@named("list")
@arg("hname", nargs='?', default=None)
def cmd_list(hname, json=False, xml=False, links=False):
    """
    list the sub-element under given hierarchical name (hname)
    """

    session_file_path = get_session_file_path()
    smc_client = SMCClient(session_file_path)

    try:
        res = smc_client.list(hname)
    except ResolveError as err:
        raise CommandError(err)
    except (SMCOperationFailure) as err:
        raise CommandError(u"(SMC): " + unicode(err))

    for name in sorted(res):
        print_fmt("{}", name)


@named("del")
def cmd_del(hname):
    """
    delete an element with its hierarchical name (hname)
    """
    #todo error
    session_file_path = get_session_file_path()
    smc_client = SMCClient(session_file_path)

    try:
        smc_elt = smc_client.get(hname)
        smc_client.delete(smc_elt)
    except ResolveError as err:
        raise CommandError(err)
    except (SMCOperationFailure) as err:
        raise CommandError(u"(SMC): " + unicode(err))



@named("apply")
@arg("filename")
@arg("-p", "--print", dest="print_only",
     help="print the payload of the smc-api request")
@arg("-pp", "--preprocess", dest="preprocess_only",
     help="print the payload of the smc-api request")
@arg("-v", '--var', dest='key_values', action='append',
     help="assign a variable (e.g. -v my_ip=10.1.1.1)", default=[], type=str)


@arg("-vf", '--var-file', dest='variable_files', action='append',
     help="read variables from a file", default=[], type=str)


@arg("-i", '--ignore-errors', dest='ignore_errors',
     help="continue script execution on error")
@arg("-d", '--delete', dest='delete_mode',
     help="delete all the resources defined in the file")
@arg("-c", '--cleanup', dest='cleanup_mode',
     help="delete all the resources before applying the config")
def cmd_apply(filename, print_only=False, preprocess_only=False,
              key_values=None, ignore_errors=False, delete_mode=False,
              cleanup_mode=False, variable_files=None):
    """
    execute a script file.
    """
    temp_file = None
    variables = {}
    for kv in key_values:
        (k, v) = kv.split("=")
        variables[k] = v

    session_file_path = get_session_file_path()
    smc_client = SMCClient(session_file_path)

    if filename=="-":
        content = sys.stdin.read()
        tf = tempfile.NamedTemporaryFile(suffix=".cnf", delete=False)
        tf.write(content.encode("utf-8"))
        tf.close()
        temp_file = tf.name
        filename = temp_file


    try:
        run_script(smc_client, filename, print_only, preprocess_only,
                   variables, variable_files,
                   ignore_errors, delete_mode, cleanup_mode)
    except (IOError) as err:
        raise CommandError(err)
    except (TemplateLookupException, SyntaxException, NameError) as err:
        raise CommandError(u"(Preprocessing): " + unicode(err))
    except (etconfig.ElementConfError) as err:
        raise CommandError(u"(Parsing): " + unicode(err))
    except (RunScriptError) as err:
        raise CommandError(u"(ScriptExec): " + unicode(err))
    except (InvalidSessionError) as err:
        raise CommandError(u"(Session): " + unicode(err))
    except (SMCOperationFailure) as err:
        raise CommandError(u"(SMC): " + unicode(err))

    if temp_file:
        os.remove(temp_file)


@named("convert")
@arg("filename")
@arg("-f", "--format", choices=["json", "yaml", "xml"],
     default="yaml", dest="fmt")
def cmd_convert(filename, fmt=None):
    """
    convert file format (to cnf, yaml or xml)
    """
    mylookup = TemplateLookup(directories=["."])
    tmpl = Template(filename=filename, lookup=mylookup)
    rendered = tmpl.render()

    elt = etconfig.loads(rendered, single_root_node=False,
                         id_mapper=etconfig.id2attr("name"))

    is_xml = (fmt == "xml")
    is_yaml = (fmt == "yaml")
    is_json = (fmt == "json")

    if is_xml:
        xml = etree.tostring(elt, encoding='utf8', pretty_print=True)
        print(xml)
    elif is_yaml:
        struct = etconfig.utils.el_to_struct(elt, False)
        print(yaml.dump(struct))
    elif is_json:
        # todo
        pass



@named("get")
# @arg("-l", "--links", dest="links", action="store_const", const=True)
@arg("-f", "--format", choices=["yaml", "xml", "conf"],
     default="conf", dest="fmt")
def cmd_get(hname, fmt=None):
    """retrieve an smc element with its hierarchical name (hname) and
    display it.
    """
    is_xml = (fmt == "xml")
    is_yaml = (fmt == "yaml")
    is_conf = (fmt == "conf")

    #todo error
    session_file_path = get_session_file_path()
    smc_client = SMCClient(session_file_path)

    try:
        smc_element = smc_client.get(hname)
    except ResolveError as err:
        raise CommandError(err)
    except (SMCOperationFailure) as err:
        raise CommandError(u"(SMC): " + unicode(err))

    elt = smc_element.data

    if is_xml:
        xml = etree.tostring(elt, encoding='utf8', pretty_print=True)
        print_fmt(xml)

    elif is_conf:
        conf = etconfig.dumps(elt, print_root=True)
        print_fmt(conf)

    elif is_yaml:
        struct = etconfig.utils.el_to_struct(elt)
        print(yaml.dump(struct))


@named("hname")
def cmd_show_hname(hname):
    """
    convert a hierarchical name (hname) into the corresponding url
    """
    session_file_path = get_session_file_path()
    smc_client = SMCClient(session_file_path)

    try:
        url = resolve_hname(smc_client.rest_client, hname)
    except ResolveError as err:
        raise CommandError(err)
    except (SMCOperationFailure) as err:
        raise CommandError(u"(SMC): " + unicode(err))

    print_fmt(url)



cmd_list = [cmd_login, cmd_logout, cmd_list, cmd_apply, cmd_del, cmd_get,
            cmd_show_hname, cmd_convert, cmd_push]
