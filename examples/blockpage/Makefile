TOOLS_DIR=../../tools

all::gen_ca apply

apply::
	${TOOLS_DIR}/smc-script apply main.cnf -c


gen_ca::
	openssl genrsa -out MyRootCA.key 2048
	openssl req -x509 -new -nodes -key MyRootCA.key -sha256 -days 1024 -out MyRootCA.pem -subj '/C=FR/ST=test1/L=test2/O=test3/CN=test3'


contact::
	${TOOLS_DIR}/smc-ssh-contact /tmp/engine_fws11.cfg 10.0.2.11



clean::
	-rm MyRootCA.key MyRootCA.pem
