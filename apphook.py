import os
import stat
import sys
import yaml
import pyfiglet
import requests
import git.util
import paramiko
import signal
import socket
import urllib3
import getpass
from tendo import singleton
from threading import Timer

instance = singleton.SingleInstance()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

inputTimeoutSec = 15
apphookVersion = '2.0.0'
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

def printOk():
    print(colors.OK,"OK",colors.ENDC)

def printFail(message=None):
    if message is None:
        print(colors.FAIL,"FAIL",colors.ENDC)
    else:
        print(colors.FAIL,"FAIL:",message,colors.ENDC)

def printHeader(message):
    print("")
    print(colors.HEADER + colors.BOLD + message + colors.ENDC)

def sigintHandler(signal, frame):
    print("")
    print (colors.OK,'Ok, Bye!',colors.ENDC)
    sys.exit(0)

def timeoutExceed():
    print("")
    printFail("Timeout exceeded")
    os.kill(os.getpid(), signal.SIGINT)

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
                printFail("Incorrect or duplicated index. Try again or go home (Ctrl+C)")
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
        printFail("Can't send message to Syslog")

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
            printFail("Only Y or N")
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
            print(url,colors.FAIL,'FAIL: Connection failed',colors.ENDC)
    else:
        printFail("Method is not provided")

def changeState(sshHost,sshPort,sshUser,sshKey,sshCommand,act_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    k = paramiko.RSAKey.from_private_key_file(sshKey)
    ssh.connect(sshHost,port=sshPort,username=sshUser,pkey=k,timeout=10)
    chan = ssh.get_transport().open_session()
    chan.exec_command(sshCommand)
    if chan.recv_exit_status() == 0:
        print(act_name,end = ' ')
        printOk()
    else:
        print(act_name,end = ' ')
        printFail()
    ssh.close()

def getVersion(sshHost,sshPort,sshUser,sshKey,sshCommand,appName):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    k = paramiko.RSAKey.from_private_key_file(sshKey)
    ssh.connect(sshHost,port=sshPort,username=sshUser,pkey=k,timeout=10)
    stdin, stdout, stderr = ssh.exec_command(sshCommand)
    for line in iter(stdout.readline, ""):
        print(appName,line, end="")
    ssh.close()

def depOve (app,env,loc,act):
    #os.environ["ANSIBLE_DISPLAY_SKIPPED_HOSTS"] = "FALSE"
    #os.environ["ANSIBLE_DISPLAY_OK_HOSTS"] = "FALSE"
    os.chmod(sshKey,stat.S_IREAD);
    if not os.path.exists('./vaultPass.txt'):
        tickTick = Timer(inputTimeoutSec, timeoutExceed)
        tickTick.daemon = True
        tickTick.start()
        vaultPass = getpass.getpass(prompt=colors.INPUT + colors.BOLD + "Password: " + colors.ENDC)
        tickTick.cancel()
        with open("vaultPass.txt", "w") as vaultPassFile:
            vaultPassFile.write("%s" % vaultPass)
    cmd = "ansible-playbook %s/approll.yml -i %s/approll.ini --extra-vars \"app_name=%s app_env=%s app_loc=%s\" --tags %s --vault-password-file vaultPass.txt -u %s --private-key %s"%(approllDir,approllDir,app,env,loc,act,sshUser,sshKey)
    os.system(cmd)

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
                    print(colors.HEADER,approllData['apps'][int(t)],colors.WARNING,approllData['envs'][int(i)].title(),colors.ENDC,approllData['locs'][int(m)].title(),colors.WARNING,approllData['acts'][int(a)].title(),colors.ENDC)
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
                    print(colors.HEADER,appName,colors.WARNING,app_env.title(),colors.ENDC,app_loc.title(),colors.WARNING,act_name.title(),colors.ENDC)
                    log_message ='{"apphook":"'+str(apphookVersion)+'","username":"'+str(username)+'","host":"'+str(hostip)+'","app":"'+appName+'","env":"'+app_env+'","loc":"'+app_loc+'","act":"'+act_name+'"}'+ "\n"
                    log(log_message)
                    
                    app_manifest_file = os.path.join(varsDir,appName + '.yml')
                    app_manifest_data = yaml.load(open(app_manifest_file,'r'), Loader=yaml.FullLoader)
                    try:
                        app_targets = app_manifest_data[appName]['targets'][app_env][app_loc]
                    except:
                        printFail('Location is not defined')
                        continue

                    if act_name == 'deploy':
                        depOve(appName,app_env,app_loc,"deploy")
                    elif act_name == 'remove':
                        depOve(appName,app_env,app_loc,"remove")
                    else:
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
                            elif act_name in ['start' ,'stop','restart']:
                                app_state = str(approllData['acts'][int(a)])
                                sshCommand = "sudo systemctl" + " " + app_state + " " + appName
                                changeState(sshHost,sshPort,sshUser,sshKey,str(sshCommand),act_name)
                            elif act_name == 'get-status':
                                sshCommand = "sudo systemctl is-active" + " " + appName
                                changeState(sshHost,sshPort,sshUser,sshKey,str(sshCommand),'is-active')
                            elif act_name == 'get-version':
                                log_file = appLogDir + appName + "/" + appName + ".log"
                                sshCommand = "sudo tail -n 1" + " " + log_file + "| cut -d ' ' -f 5"
                                getVersion(sshHost,sshPort,sshUser,sshKey,str(sshCommand),appName)
                            else:
                                printFail()
                                sys.exit(1)

signal.signal(signal.SIGINT, sigintHandler)
main()
sys.exit(0)