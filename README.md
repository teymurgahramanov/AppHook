# AppHook
Tool for managing Java application instances which deployed using AppRoll.

## Features:
* Perform actions on multiple or all Applications, Environments and Sites at once
* Manage systemd service (start,stop,restart,is-active)
* Healthcheck via HTTP
* Get current version of Application
* Logging to Syslog
* Prevent multiple instance run at same time

## Requirements:
* User with key authentication and restricted sudo privileges (Currently: /bin/systemctl,/bin/tail) on application servers.
* Access to [AppRoll](https://github.com/teymurgahramanov/AppRoll) repository
* User which will use AppHook must have rw privileges, to be able to clone AppRoll repository.
* Your ```apphook.yml``` in AppRoll must have correct structure and actual data
 
## How to use
### Directly
1. Create virtual environment and install required modules
2. Place user key in ./ssh
3. Configure ./apphook.yml
4. ```python apphook.py"```
5. Start and follow instructions (May take some time until clone AppRoll)

### Docker
1. Build image
2. docker run --rm --name apphook --env APPHOOK_USER --env APPHOOK_USER_IP -it imagerepo/apphook:latest

![Alt Text](./.static/apphook.gif)

* Developed and tested with:
    - Python 3.6

___
https://t.me/teymurgahramanov \
https://t.me/ITBlogbyTeymur
