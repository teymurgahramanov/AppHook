import os
import sys
import yaml
import pyfiglet
import requests
import git.util
import paramiko
import signal
import socket
import urllib3
from tendo import singleton
from threading import Timer

instance = singleton.SingleInstance()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

inputTimeoutSec = 10
apphookVersion = '1.0.8'
apphookData = yaml.load(open("./apphook.yml",'r'), Loader=yaml.FullLoader)
approllUrl = apphookData['approll']['url']
approllDir = apphookData['approll']['dir']
varsDir = apphookData['approll']['varsDir']
apphookFile = apphookData['approll']['apphookFile']
sshUser = apphookData['ssh']['user']
sshKey = apphookData['ssh']['privKey']
syslogHost = apphookData['syslog']['host']
syslogPort = apphookData['syslog']['port']
appLogDir = apphookData['structure']['appLogDir']

if os.path.exists(approllDir) and os.path.isdir(approllDir):
    g = git.cmd.Git(approllDir)
    g.pull()
else:
    git.Git().clone(approllUrl,approllDir)

approllData = yaml.load(open(apphookFile,'r'), Loader=yaml.FullLoader)

class colors:
    HEADER = '\033[95m'
    INPUT = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'

def sigintHandler(signal, frame):
    print("")
    print (colors.OK,'Ok, Bye!',colors.ENDC)
    sys.exit(0)

def timeoutExceed():
    print("")
    print(colors.FAIL,'Timeout exceeded',colors.ENDC)
    os.kill(os.getpid(), signal.SIGINT)
    
def printOk():
    print(colors.OK + "OK" + colors.ENDC)

def printFail():
    print(colors.FAIL + "FAIL" + colors.ENDC)

def printError(message):
    print("")
    print(colors.FAIL + message + colors.ENDC)
    print(colors.FAIL + "Try again or go home (Ctrl+C)" + colors.ENDC)
    print("")
    
def printHeader(message):
    print("")
    print(colors.HEADER + colors.BOLD + message + colors.ENDC)

def getUsername():
    userhome = os.path.expanduser('~')          
    username = os.path.split(userhome)[-1]
    return username     

def getHostip():
    hostname = socket.gethostname()    
    ip = socket.gethostbyname(hostname)
    hostip = str(hostname) + ' ' + str(ip)
    return hostip

def start():
    banner = pyfiglet.figlet_format("AppHook")
    print(colors.INPUT + colors.BOLD + banner + apphookVersion + colors.ENDC)
    print("")
    print(colors.WARNING,'#' * 10,'README','#' * 10,colors.ENDC)
    print('- Can work only in single instance')
    print('- To select multiple items, separate numbers by comma. Example: 2,9,5')
    print('- To select all items, type 220595')
    print('- Input timeout is',inputTimeoutSec,'seconds')
    print(colors.WARNING,'#' * 10,'README','#' * 10,colors.ENDC)

def loadVars():
    varsLoad = yaml.load(open(apphookFile,'r'), Loader=yaml.FullLoader)
    return varsLoad

def menu(menu,list):
    while True:
        tickTick = Timer(inputTimeoutSec, timeoutExceed)
        tickTick.daemon = True
        printHeader ("Choose" + ' ' + menu + '(s)' + ':')
        for index, value in enumerate(approllData.get(list)):
            print(index, value)
        tickTick.start()
        inputvar = input(colors.INPUT + colors.BOLD + "Number: " + colors.ENDC).split(',')
        tickTick.cancel()
        if inputvar == ['220595']:
            inputvar = [index for index, value in enumerate(approllData.get(list))]
            print(colors.WARNING,'All selected',colors.ENDC)
            printOk()
            break
        else:
            try:
                checkinput = [int(i.strip()) for i in inputvar]                    
                checkindex = [approllData[list][int(i)] for i in inputvar]
                checkduplicate = any(inputvar.count(i) > 1 for i in inputvar)
                if checkduplicate == True:
                    raise Exception
            except:
                tickTick.cancel()
                printFail()
                printError("Incorrect or Duplicated index. If multiple, separate with comma.")
                continue
        printOk()
        break
    return inputvar

def log(message):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((syslogHost, syslogPort))
        s.sendall(message.encode('utf-8'))
    except:
        print(colors.FAIL,"Can't send message to Syslog",colors.ENDC)

def approve():
    while True:
        tickTick = Timer(inputTimeoutSec, timeoutExceed)
        tickTick.daemon = True
        tickTick.start()
        answer = input(colors.INPUT + colors.BOLD + "OK? (Y/N): " + colors.ENDC)
        tickTick.cancel()
        if answer == 'Y':
            return answer
            break
        elif answer == 'N':
            sys.exit(0)
        else:
            tickTick.cancel()
            print(colors.FAIL,"Only Y or N",colors.ENDC)
            continue

def healthcheck(host,port,endpoint,method,response):
    url="http://" + host + ":" + port + endpoint
    if method != "" and method == "GET":
        try: 
            request=requests.get(url,timeout=5)
            if str(request.status_code) == response:
                print(url,colors.OK,str(request.status_code),'OK',colors.ENDC)
            else:
                print(url,colors.WARNING,str(request.status_code),'WARNING',response,'EXPECTED',colors.ENDC)
        except:
            print(url,colors.FAIL,'FAIL',colors.ENDC)
    else:
        print(colors.WARNING,'Method not provided',colors.ENDC)

def chstate(sshHost,sshPort,sshUser,sshKey,sshCommand):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    k = paramiko.RSAKey.from_private_key_file(sshKey)
    ssh.connect(sshHost,port=sshPort,username=sshUser,pkey=k)
    chan = ssh.get_transport().open_session()
    chan.exec_command(sshCommand)
    if chan.recv_exit_status() == 0:
        print(sshCommand,chan.recv_exit_status(),end = ' ')
        printOk()
    else:
        print(sshCommand,chan.recv_exit_status(),end = ' ')
        printFail()
    ssh.close()

def version(sshHost,sshPort,sshUser,sshKey,sshCommand,appName):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    k = paramiko.RSAKey.from_private_key_file(sshKey)
    ssh.connect(sshHost,port=sshPort,username=sshUser,pkey=k)
    stdin, stdout, stderr = ssh.exec_command(sshCommand)
    for line in iter(stdout.readline, ""):
        print(appName,line, end="")
    ssh.close()

def main():
    
    start()
    username = os.getenv('APPHOOK_USER', getUsername())
    hostip = os.getenv('APPHOOK_USER_IP', getHostip())

    app_index = menu("application","apps")
    env_index = menu("environment","envs")
    loc_index = menu("location","locs")
    act_index = menu("action","acts")

    print("")
    print(colors.WARNING,"FOLLOWING ACTIONS WILL BE PERFORMED!",colors.ENDC)
    for t in app_index:
        for i in env_index:
            for m in loc_index:
                for a in act_index:
                    print(approllData['apps'][int(t)],colors.WARNING,approllData['envs'][int(i)],colors.ENDC,approllData['locs'][int(m)],colors.WARNING,approllData['acts'][int(a)],colors.ENDC)
    approve()
    
    for t in app_index:
        for i in env_index:
            for m in loc_index:
                for a in act_index:

                    appName = approllData['apps'][int(t)]
                    app_env = approllData['envs'][int(i)]
                    app_loc = approllData['locs'][int(m)]
                    act_name = approllData['acts'][int(a)]

                    print("")
                    print(colors.HEADER,appName,app_env,app_loc,colors.WARNING,act_name,colors.ENDC)
                    log_message ='{"username":"'+str(username)+'","host":"'+str(hostip)+'","app":"'+appName+'","env":"'+app_env+'","loc":"'+app_loc+'","act":"'+act_name+'"}'+ "\n"
                    log(log_message)
                    
                    app_manifest_file = os.path.join(varsDir,appName + '.yml')
                    app_manifest_data = yaml.load(open(app_manifest_file,'r'), Loader=yaml.FullLoader)
                    try:
                        app_targets = app_manifest_data[appName]['targets'][app_env][app_loc]
                    except:
                        print(colors.FAIL,'Location',app_env,app_loc,'for',appName,'is not defined',colors.ENDC)
                        continue

                    for target in app_targets:
                        print(colors.UNDERLINE,target.split(':')[0],colors.ENDC)
                        sshHost = target.split(':')[0]
                        sshPort = target.split(':')[1]
                        if act_name == 'check':
                            host = target.split(':')[0]
                            healthcheck(
                                host,
                                str(app_manifest_data[appName]['ports']['http']),
                                str(app_manifest_data[appName]['healthcheck']['endpoint']),
                                str(app_manifest_data[appName]['healthcheck']['method']),
                                str(app_manifest_data[appName]['healthcheck']['response'])
                            )
                        elif act_name in ['start' ,'stop','restart','is-active']:
                            app_state = str(approllData['acts'][int(a)])
                            sshCommand = "sudo systemctl" + " " + app_state + " " + appName
                            chstate(sshHost,sshPort,sshUser,sshKey,str(sshCommand))
                        elif act_name == 'get-version':
                            log_file = appLogDir + appName + "/" + appName + ".log"
                            sshCommand = "sudo tail -n 1" + " " + log_file + "| cut -d ' ' -f 5"
                            version(sshHost,sshPort,sshUser,sshKey,str(sshCommand),appName)
                        else:
                            printFail()
                            sys.exit(1)

signal.signal(signal.SIGINT, sigintHandler)
main()
sys.exit(0)
