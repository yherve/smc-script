
single_fw/fws11/internal_gateway/fws11 - Primary/internal_endpoint/10.0.3.11

## features to add

### exit status is incorrect

on error

### read variable from file or env

#### using env variable

similar to terraform https://www.terraform.io/docs/configuration/variables.html

    export CNF_VAR_ip="1.2.3.4"

makes 'ip' variable available

#### using file

- matching *.cnfvars
- '--var-file='

### bug: auto login after session expired does not work

Unexpected error 'UnicodeEncodeError'

### wait for policy to be published/report error

policy push from the cli with progress bar

### hname containing regexp or wildcard

not sure for the syntax:

    '#log_server/~LogServer'
    '#log_server/LogServer*'
    '#log_server/LogServer.+'


### filter get result with xpath

using an xpath expression

    smc-script get 'fw_policy/AAAA/fw_ipv4_access_rules/Rule @106.4' -q "action['@action']"

or simply a dotted notation

    smc-script get 'fw_policy/AAAA/fw_ipv4_access_rules/Rule @106.4' -q "destinations.dst"

### simplify get result

skip

- false values
- links
- key, read_only, system

### handle concurrent update exception

reload with correct etag, reapply pending changes and reattempt update

### href to hname in get display (reverse resolve in get)

- at least for elements

### 'get' cli command outputs python api

- generates automatically the python script of an existing element

### 'get' with wildcard

eg get all the access rules

    smc-script get 'fw_policy/AAAA/fw_ipv4_access_rules/*'


### deal with api version

- list available versions on the cli
- make the working version available in a variable to have conditionals

### write doc

!

### write tests

- check exit status
- at least run automatically all the examples

### log cli command

- view
- and control the log verbosity/shows log
- delete log

### bash completion

-

### config script in yaml

-

### config script in json

-

### automatically prefix all names

-

### scripted login/logout

-

### cache resolved hname for performance

-

### python3 support

-


## nice to have

- pluggable template engine (jinja2...)

## ansible integration

write the config as ansible playbook

eg

https://github.com/F5Networks/f5-ansible/blob/devel/examples/0000-getting-started/playbook.yaml

## smc-mount

mount the smc conf as a fusefs. Navigate in the config using regular
unix commands:
- cd
- cat
- rm
- mv


## examples

- virtual engine
- policy based vpns
- cloud scaleset (sg_smc_create_engine replacement)

---

## moka template, variable expand command line

    host "myhost1" {
        ipv6_address = ${ip}
    }

    smc-script run myscript.conf --ip 1.2.3.4

## done

- command in conf file (eg add route)
- update object (eg routing table)
- test add dns server
- test add default route
- test dhcp relay
- test cluster
- cloud use case (sg_smc_create_engine replacement)
- logging file ~/.config/smc-script/
- session ~/.config/smc-script/session
- restore session ~/.config/smc-script/session
- command execute
- update
- get
- logout
- list
- autologin using ~/.smcrc (case no session/session expired)
- https from cli
- login specify version
- logout
- error handling
- delete mode, where the script 'apply' deletes all the objects
- apply get from stdin: here-doc command from bash
- strict mode  (stop on first error)
- improve output of 'apply' to see which command has failed
- login fail 401 proper displayed message
- list hname at any level
- hname resolve code more generic
- rb vpn example
