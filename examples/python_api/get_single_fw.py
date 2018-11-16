"""This example shows how to use the api to create a fw, the retrieve
it with its 'hname'
"""

from smcscript.api import SMCClient, cnf_elt

client = SMCClient()

# uses login information in ~/.smcrc
client.login()

# list all the elements from the smc server
fw_list = client.list("#single_fw")
print(fw_list)

# get an element from the smc server
fw1 = client.get("#single_fw/myfw1")
print(fw1)

# you retrieve information from the element using xpath queries
print("nodeid", fw1.get("firewall_node/@nodeid"))
print("nodename", fw1.get("/single_fw/firewall_node/@name"))
print("address", fw1.get("//single_node_interface/@address"))
print("DNS addresses", fw1.get_all("//domain_server_address/@value"))


client.logout()
