
single_fw/fws11/internal_gateway/fws11 - Primary/internal_endpoint/10.0.3.11

## features to add


- auto login after session expired does not work
- simplify get result (eg by skipping false values, links...)
- read variables from a file
- concurrent update exception
- href to hname in get display (reverse resolve in get)
- get element and display as python api (lxml builder)
- list available versions/make the version available in a mako variable
- write doc !
- write tests !
- log command to view and control the log verbosity/shows log
- config script in yaml
- config script in json
- bash completion
- automatically prefix all names
- scripted login/logout
- hname with regexp or wildcard, eg ~log_server/LogServer.*
- cache resolved hname

## nice to have

- filter get result with xpath
- pluggable template engine (jinja2...)

## ansible

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


## test/examples

- test virtual engine
- test vpn
- cloud use case scaleset (sg_smc_create_engine replacement)

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
