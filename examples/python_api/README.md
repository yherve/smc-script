List of examples
------------------

- create_single_fw.py shows how to create a single_fw using the api
- create_single_fw_lxml.py shows how to create a single_fw using the lxml builder


Running the examples
-----------------------

1. install the smc-script library in a virtual env

    cd <smc-script-repo>
    . use_venv.sh

or if you wish to install the library in your own ~/.local

    cd <smc-script-repo>
    pip install --user -r ./requirements.txt

2. create the file with the login info

example:

    cat ~/.smcrc

    #-*- conf -*-
    [smc]
    smc_address=192.168.100.7
    smc_apikey=xxxxxxxxxxxxxxx
    api_version=6.4
    smc_port=8082
    smc_ssl=False
    verify_ssl=False
    ssl_cert_file=''

3. run the example

example

    python ./create_single_fw.py
