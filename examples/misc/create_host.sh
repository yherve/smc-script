#!/bin/bash

set -eu

export PATH=../../dist:$PATH

NWNAME=mynw1
smc-script login -a

cat <<EOF |  smc-script apply -
resource {
   network $NWNAME { ipv6_network = fd99::/64 }
}
EOF

smc-script get network/$NWNAME
smc-script del network/$NWNAME
