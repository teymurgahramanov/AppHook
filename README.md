# AppHook
Tool for managing AppRolled instances.

## Features:
* Perform actions on multiple or all Applications, Environments and Sites at one time
* Deploy and remove instances
* Manage systemd service (start,stop,restart,status)
* HTTP Healthcheck
* Get current version of Application
* Logging to Syslog server

## Requirements:
* User with key authentication and sudo privileges on target servers.
* Access to AppRoll repository
* Docker Engine
 
## Usage
1. Configure AppRoll
2. Place user key in ./ssh
3. Configure apphook.yml
4. ```docker build apphook .```
5. ```docker run --rm --name apphook -it apphook```

![Alt Text](./.static/apphook.gif)
