smc-script
============================

version number: 0.9
author: Yann Hervé

Overview
--------

smc-script allows to configure the forcepoint next-gen firewall using
simple configuration files 'cnf', similar to terraform language (hcl)

For more flexibility, These files can be preprocessed using the mako
template language

Example:

The following example installs a policy that allow all the traffic.

    # cat create_policy.cnf

```HCL
    resource "#fw_policy" {
        fw_policy "mypolicy" {
            template "#fw_template_policy/Firewall Template";
        }
    }

    resource "#fw_policy/mypolicy/fw_ipv6_access_rules" {
        fw_ipv6_access_rule "allow_all" {
            action.action = allow
            destinations.any = true
            sources.any = true
            services.any = true
        }
    }
```

to install the policy, simply enter the following commands

    $ smc-script login -k <apikey> <smc-ip-address>
    $ smc-script apply create_policy.cnf


Installing
-----------------

### prebuild binary

Download standalone smc-script for linux 64bits (built on ubuntu 18.04) [Here](https://github.com/yherve/smc-script/files/3743757/smc-script.zip) and place it in your PATH (e.g. ~/bin)

### run in dev environment

requirements: python2.7, pip and virtualenv

    git clone https://github.com/yherve/smc-script
    . use_venv.sh

this scripts creates a virtualenv, installs requirements and adds an
alias command 'smc-script' that runs directly from the source tree

### building a standalone executable

    git clone https://github.com/yherve/smc-script
    make

the executable is in ./dist/smc-script


Documentation
------------------

Documentation is available in the wiki: <https://github.com/yherve/smc-script/wiki>
