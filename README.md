# AppHook
Tool for managing AppRolled instances.

## Features:
* Perform actions on multiple or all Applications, Environments and Sites at once
* Deploy and remove instances
* Manage systemd service (start,stop,restart)
* Get service status
* HTTP Healthcheck
* Get current version of Application
* Logging to Syslog
* Prevent multiple instance run at same time

## Requirements:
* User with key authentication and sudo privileges on target servers.
* Access to AppRoll repository
* Docker Engine > 19
 
## How to use

1. Configure AppRoll
2. Configure apphook.yml
2. Place user key in ./ssh
3. docker build apphook .
4. docker run --rm --name apphook --env APPHOOK_USER --env APPHOOK_USER_IP -it apphook

![Alt Text](./.static/apphook.gif)
