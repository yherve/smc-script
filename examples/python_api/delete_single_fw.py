"""This example shows how to delete an element with its 'hname'
"""
import sys

from smcscript.api import SMCClient

client = SMCClient()
client.login()
client.delete("#single_fw/myfw1")
client.logout()
