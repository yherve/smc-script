
  
  
                                   +-------------+
                                   |             |
                                   |    smc      |
                                   |             |
                                   |             |
        +--+--+-+---+              +------+------+                 +------------+
        |           |                     |                        |            |
        | browser   |                     |mgtnw             +-----+web resource|
        |           |                     |                  |     |            |
        |           |                     |                  |     |            |
        +-----+-----+               192.168.100.10           |     +------------+
              |                     +-----+----+             |
              |              +------+----------+-----+       |lan2svr
              |              | +--------+ +--------+ |       |
              |              | |        | |        | |       |
      lan1clt |              | |fwn11   | | fwn12  | |       |
              +--------------+ +        +-+        + +-------+
               192.168.101.10| |        | |        | |192.168.102.10
                             | +--------+ +--------+ |
                             |         fwc10         |
                             +-----------------------+


## description

creation of:

- networks
- cluster with 2 nodes and 3 interfaces (cvi/ndi) and default route
- policy any/any/allow
- ldap user
- sso profile
- rwp service
- rwp policy
- rwp portal

### Note 1

it is necessary to manually activate the user db replication
(I could not find a way to do it with the rest api)

### Note 2

For simplicity the 'admin' interface (192.168.100.10) is used for
everything (control, hbeat, rwp endpoint)

## usage

to create the config in the smc

    $ smc-script login -k <apikey> <smc-ip-address>
    $ smc-script apply main.cnf

to make an initial contact and bind the license

    $ smc-script apply initial_contact.cnf

(engine.cfg for both nodes can be found under /tmp)
