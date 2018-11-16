smc-script
============================

version number: 0.0.1
author: Yann Hervé

Overview
--------

smc-script allows to configure the forcepoint next-gen firewall using
simple configuration files. Several format are supported
- cnf: similar to terraform language (hcl)
- xml
- yaml: future release
- json: future release

For more flexibility, These files can be preprocessed using the mako
template language

Example:

The following example installs a policy that allow all the traffic.

    # cat create_policy.cnf
    create fw_policy {
        fw_policy "mypolicy" {
            template "#fw_template_policy/Firewall Template";
        }
    }

    create fw_ipv6_access_rules {
        target="#fw_policy/mypolicy"
        fw_ipv6_access_rule "allow_all" {
            action.action = allow
            destinations.any = true
            sources.any = true
            services.any = true
        }
    }

to install the policy, simply enter the following commands

    $ smc-script login -k <apikey> <smc-ip-address>
    $ smc-script run create_policy.cnf
