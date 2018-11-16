

## login

tip: prevent bash history to keep your api keys using this command (or
simply start line with a space)

    export HISTIGNORE="smc-script login*"

### basic command

connect to the smc at 192.168.100.7 on HTTP using default port 8082

    smc-script login -k XXXXX 192.168.100.7

On success, a session file is created with default name ~/.smc-script/last-session
