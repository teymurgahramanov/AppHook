# AppHook
Tool for managing Java application instances which deployed using AppRoll.

## Requirements:
* Python > 3.6

## How to setup:
1. Clone this repo
2. Create virtual environment and install required modules
2. Create user with key authentication and restricted sudo privileges (In my case: /bin/systemctl,/bin/tail) on application servers.
3. Place user key in to ./ssh
4. Configure ./apphook.yml in aproriate way
5. (Recommended) Set alias: \
~~~alias apphook="clear; /path/apphook/.venv/bin/python /path/apphook/apphook.py"
~~~
**!Ensure you that user which will use AppHook has rw privileges on directory. It needed for git.**


## How to use
Start and follow instructions ```¯\_(ツ)_/¯```