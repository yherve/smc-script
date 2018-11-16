import sys
from smcscript.api import SMCClient, SMCElement, cnf_elt
from lxml.builder import E as elt
import etconfig

client = SMCClient()
client.login()


fw1 = client.get("#single_fw/myfw1")
print(fw1.data.get("is_config_encrypted"))

# simple case, change attributes at the root
fw1.set_values(is_config_encrypted = True)


fw1.set_values("//domain_server_address[@value='8.8.4.4']",
               value="1.1.1.1", rank=2.0)

fw1.remove("//domain_server_address[@value='8.8.8.8']")

fw1.add("//domain_server_addresses",
        elt.domain_server_address(value="1.1.0.0", rank="3.0"),
        elt.domain_server_address(value="9.9.9.9", rank="1.0"))

# fw1.apply_changes()
# print(fw1.data.get("is_config_encrypted"))
# addresses = fw1.data.xpath("domain_server_addresses")
# print(etconfig.el_to_conf(addresses[0]))

client.update(fw1)
client.logout()
sys.exit(0)
