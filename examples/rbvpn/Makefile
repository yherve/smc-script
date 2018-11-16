
TOOLS_DIR=../../tools

all::
	${TOOLS_DIR}/smc-script apply main.cnf -c
	${TOOLS_DIR}/smc-ssh-contact /tmp/engine_tst11.cfg
	${TOOLS_DIR}/smc-ssh-contact /tmp/engine_tst12.cfg

clean::
	${TOOLS_DIR}/smc-script apply main.cnf -d
