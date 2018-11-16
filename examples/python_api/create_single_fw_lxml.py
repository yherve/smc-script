"""
This example shows how to use the api with lxml builder.
Note that the sub-element must always appear before the attributes.
"""

from smcscript.api import SMCClient
from lxml.builder import E as elt

client = SMCClient()
client.login()

data=elt.single_fw(
    elt.firewall_node(name="myfw1node", nodeid="1"),
    elt.physical_interface(
        elt.single_node_interface(
            address="192.168.100.7", network_value="192.168.100.0/24",
            nicid="1", nodeid="1",auth_request="true", primary_mgt="true"),
        name="Interface 1", interface_id="1"),
    name="myfw1", log_server_ref="#log_server/[0]")

client.create(data)
client.logout()
