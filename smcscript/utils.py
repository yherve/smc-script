# -*- coding: utf-8 -*-
"""
various utils functions
"""
from __future__ import print_function, unicode_literals

import os
import sys
import logging
import pickle

# pylint: disable=invalid-name
logger = logging.getLogger(__name__)


def get_config_dir():
    """
    return path of directory containing smc-script files
    (usually ~/.config/smc-script)
    """
    smcscript_dir = os.path.expanduser('~/.config/smc-script')

    if not os.path.isdir(smcscript_dir):
        os.makedirs(smcscript_dir)
        os.chmod(smcscript_dir, 0o755)

    return smcscript_dir


def save_session(sess, session_file_path=None):
    """save session.

    sess is an instance of smcscript.session.Session
    return True on success
    """
    if not session_file_path:
        config_dir = get_config_dir()
        session_file_path = os.path.join(config_dir, "session")

    try:
        logger.info("Trying to save session to '%s'", session_file_path)
        with open(session_file_path, 'wb') as f:
            pickle.dump(sess, f)
        os.chmod(session_file_path, 0o600)
        return True

    # pylint: disable=broad-except
    except Exception as e:
        logger.exception("Failed to save session: %s", str(e))
        return False


def load_session(session_file_path=None):
    """load session.

    return instance of smcscript.session.Session or None on error

    :param str session_file_path: path of a file containing a
    serialized session

    :returns: return instance of smcscript.session.Session or None on error
    :rtype: smcscript.session.Session

    """
    sess = None
    if not session_file_path:
        config_dir = get_config_dir()
        session_file_path = os.path.join(config_dir, "session")

    logger.debug("Trying to restore session from '%s'", session_file_path)
    if not os.path.isfile(session_file_path):
        logger.warn("No session to restore from '%s'", session_file_path)
        return None

    try:
        with open(session_file_path, 'rb') as f:
            sess = pickle.load(f)
        logger.info("Session restored successfully for '%s'", sess.url)
    # pylint: disable=broad-except
    except Exception as exc:
        logger.error("Failed to restore session from '%s': %s",
                     session_file_path, exc)

    return sess


def get_session_file_path():
    """
    return path of file containing the serialized session
    """
    config_dir = get_config_dir()
    session_file_path = os.path.join(config_dir, "session")
    return session_file_path

#----------------------------------------------------------------------
# utils
#----------------------------------------------------------------------

def print_fmt(fmt, *args, **kwargs):
    """
    print and format in one function
    """
    if not args and not kwargs:
        cmd_fmt = fmt
    else:
        cmd_fmt = fmt.format(*args, **kwargs)
    print(cmd_fmt)



def print_err(fmt, *args, **kwargs):
    """
    print to stderr and format in one function
    """
    print_fmt(fmt, *args, file=sys.stderr, **kwargs)

def print_values(*args, **kwargs):
    """
    print a list of key/values
    """
    sep = " "
    lst1 = ["{}".format(str(a)) for a in args]
    lst2 = ["{}={}".format(k, v) for k, v in kwargs.items()]

    print(sep.join(lst1 + lst2))



def cleanup_element_xml(elt):
    """
    remove useless info
    """
    try:
        # cleanup, remove useless info
        for lk in elt.iter("links"):
            lk.getparent().remove(lk)
        del elt.attrib["key"]
        del elt.attrib["system"]
        del elt.attrib["read_only"]
        # pylint: disable=bare-except
    except:
        pass


# def _remove_links_from_elt(elt):
#     for lk in elt.iter("links"):
#         lk.getparent().remove(lk)
