#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
smc-script main
"""
from __future__ import print_function, unicode_literals

import logging
import os
import sys
import argh

from smcscript.utils import get_config_dir, print_err
from smcscript.exceptions import InvalidSessionError, CommandError

from smcscript.commands import cmd_list

# pylint: disable=invalid-name
logger = logging.getLogger(__name__)


def main():
    """entry point"""
    smcscript_dir = get_config_dir()

    logfile_path = os.path.join(smcscript_dir, "smcscript.log")
    # os.remove(logfile_path)

    logging.basicConfig(filename=logfile_path, level=logging.DEBUG)
    os.chmod(logfile_path, 0o600)

    logger.info('-'*60)

    # if first argument is a file, we assume apply command
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        sys.argv.insert(1, 'apply')

    logger.info("Command: %s", ' '.join(sys.argv[1:]))

    parser = argh.ArghParser()
    parser.add_commands(cmd_list)
    try:
        parser.dispatch()

    # pylint: disable=broad-except
    except (CommandError) as err:
        print_err("Error: {}", unicode(err))
    except (InvalidSessionError) as err:
        print_err("Error: {}", unicode(err))
    except Exception as e:
        print_err("Unexpected error '{}': {}\n(see {})", type(e).__name__, e, logfile_path)
        logger.debug("Got unexpected exception: %s", type(e))
        logger.exception(e)

if __name__ == '__main__':
    main()
