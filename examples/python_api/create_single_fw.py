"""This example shows how to use the api to create a fw, the retrieve
it with its 'hname'
"""

from smcscript.api import SMCClient, cnf_elt

client = SMCClient()
client.login()

data=cnf_elt("""
    single_fw "myfw1" {
        log_server_ref="#log_server/[0]"
        firewall_node "myfw1node" {
            nodeid=1
        }
        physical_interface "Interface 1" {
            interface_id=1
            single_node_interface {
                address=192.168.100.7
                network_value=192.168.100.0/24
                nicid=1; nodeid=1
                auth_request=true; primary_mgt=true
            }
        }
        domain_server_addresses {
            domain_server_address {value=8.8.8.8; rank=1.0}
            domain_server_address {value=8.8.4.4; rank=0.0}
        }
    }
    """)

client.create(data)

# get by hname, fw1 is an instance of SMCElement
fw1 = client.get("#single_fw/myfw1")

client.execute("#single_fw/myfw1", "add_route",
               params = dict(gateway="192.168.100.1",
                             network="0.0.0.0/0"))

client.execute(fw1, "firewall_node/myfw1node/bind")
res = client.execute(fw1, "firewall_node/myfw1node/initial_contact")
print(res)
client.logout()
