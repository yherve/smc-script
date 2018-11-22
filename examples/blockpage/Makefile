

gen_ca::
	openssl genrsa -out MyRootCA.key 2048
	openssl req -x509 -new -nodes -key MyRootCA.key -sha256 -days 1024 -out MyRootCA.pem -subj '/C=FR/ST=test1/L=test2/O=test3/CN=test3'

clean::
	-rm MyRootCA.key MyRootCA.pem
