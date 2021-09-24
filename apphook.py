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

try:
    instance = singleton.SingleInstance()
except:
    sys.exit(1)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

apphook_version = '0.0.1'
apphook_properties = yaml.load(open("./apphook.yml",'r'), Loader=yaml.FullLoader)
approll_dir = apphook_properties['approll']['dir']
vars_dir = apphook_properties['approll']['vars_dir']
vars_file = apphook_properties['approll']['vars_file']
ssh_user = apphook_properties['ssh']['user']
ssh_key = apphook_properties['ssh']['priv_key']
syslog_host = apphook_properties['syslog']['host']
syslog_port = apphook_properties['syslog']['port']
app_log_dir = apphook_properties['structure']['app_log_dir']

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'

def sigint_handler(signal, frame):
    print("")
    print (colors.OKGREEN,'Ok, Bye!',colors.ENDC)
    sys.exit(0)
    
def print_ok():
    print(colors.OKGREEN + "OK" + colors.ENDC)

def print_fail():
    print(colors.FAIL + "FAIL" + colors.ENDC)

def print_error(message):
    print("")
    print(colors.FAIL + message + colors.ENDC)
    print(colors.FAIL + "Try again or go home (Ctrl+C)" + colors.ENDC)
    print("")
    
def print_header(message):
    print("")
    print(colors.HEADER + colors.BOLD + message + colors.ENDC)

def get_username():
    userhome = os.path.expanduser('~')          
    username = os.path.split(userhome)[-1]
    return username     

def get_hostip():
    hostname = socket.gethostname()    
    ip = socket.gethostbyname(hostname)
    hostip = str(hostname) + ' ' + str(ip)
    return hostip

def start():
    banner = pyfiglet.figlet_format("AppHook")
    approll_url = apphook_properties['approll']['url']
    approll_dir = apphook_properties['approll']['dir']
    print(colors.OKBLUE + colors.BOLD + banner + apphook_version + colors.ENDC)
    if os.path.exists(approll_dir) and os.path.isdir(approll_dir):
        g = git.cmd.Git(approll_dir)
        g.pull()
    else:
        git.Git().clone(approll_url,approll_dir)

def load_vars():
    vars_load = yaml.load(open(vars_file,'r'), Loader=yaml.FullLoader)
    return vars_load

vars_data = load_vars()

def menu(menu,list):
    while True:
        print_header ("Choose" + ' ' + menu + ':')
        for index, value in enumerate(vars_data.get(list)):
            print(index, value)
        inputvar = input(colors.OKBLUE + colors.BOLD + "Number: " + colors.ENDC).split(',')
        try:
            checkinput = [int(i.strip()) for i in inputvar]                    
            checkindex = [vars_data[list][int(i)] for i in inputvar]
            checkduplicate = any(inputvar.count(i) > 1 for i in inputvar)
            if checkduplicate == True:
                raise Exception
        except:
            print_fail()
            print_error("Incorrect or Duplicated index. If multiple, separate with comma.")
            continue
        print_ok()
        break
    return inputvar

def log(message):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((syslog_host, syslog_port))
        s.sendall(message.encode('utf-8'))
    except:
        print(colors.FAIL,"Can't send message to Syslog",colors.ENDC)

def approve():
    while True:
        answer = input(colors.OKBLUE + colors.BOLD + "OK? (Y/N): " + colors.ENDC)
        if answer == 'Y':
            return answer
            break
        elif answer == 'N':
            sys.exit(0)
        else:
            print(colors.FAIL,"Only Y or N",colors.ENDC)
            continue

def healthcheck(host,port,endpoint,method,response):
    url="http://" + host + ":" + port + endpoint
    if method != "" and method == "GET":
        try: 
            request=requests.get(url,timeout=5)
            if str(request.status_code) == response:
                print(url + colors.OKGREEN + ' OK ' + str(request.status_code) + colors.ENDC)
            else:
                print(url + colors.WARNING + ' WARNING ' + str(request.status_code) + ' EXPECTED ' + response + colors.ENDC)
        except:
            print(url + colors.FAIL + ' FAIL ' + colors.ENDC)
    else:
        print(colors.WARNING + 'Method not provided' + colors.ENDC)

def chstate(ssh_host,ssh_port,ssh_user,ssh_key,ssh_command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    k = paramiko.RSAKey.from_private_key_file(ssh_key)
    ssh.connect(ssh_host,port=ssh_port,username=ssh_user,pkey=k)
    chan = ssh.get_transport().open_session()
    chan.exec_command(ssh_command)
    if chan.recv_exit_status() == 0:
        print(ssh_command,chan.recv_exit_status(),end = ' ')
        print_ok()
    else:
        print(ssh_command,chan.recv_exit_status(),end = ' ')
        print_fail()
    ssh.close()

def version(ssh_host,ssh_port,ssh_user,ssh_key,ssh_command,app_name):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    k = paramiko.RSAKey.from_private_key_file(ssh_key)
    ssh.connect(ssh_host,port=ssh_port,username=ssh_user,pkey=k)
    stdin, stdout, stderr = ssh.exec_command(ssh_command)
    for line in iter(stdout.readline, ""):
        print(app_name,line, end="")
    ssh.close()

def main():
    
    start()
    username = get_username()
    hostip = get_hostip()

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
                    print(colors.HEADER,vars_data['apps'][int(t)],vars_data['envs'][int(i)],vars_data['locs'][int(m)],colors.WARNING,vars_data['acts'][int(a)],colors.ENDC)
    approve()
    
    for t in app_index:
        for i in env_index:
            for m in loc_index:
                for a in act_index:

                    app_name = vars_data['apps'][int(t)]
                    app_env = vars_data['envs'][int(i)]
                    app_loc = vars_data['locs'][int(m)]
                    act_name = vars_data['acts'][int(a)]

                    print("")
                    print(colors.HEADER,app_name,app_env,app_loc,colors.WARNING,act_name,colors.ENDC)
                    log_message ='{"username":"'+str(username)+'","host":"'+str(hostip)+'","app":"'+app_name+'","env":"'+app_env+'","loc":"'+app_loc+'","act":"'+act_name+'"}'+ "\n"
                    log(log_message)
                    
                    app_manifest_file = os.path.join(vars_dir,app_name + '.yml')
                    app_manifest_data = yaml.load(open(app_manifest_file,'r'), Loader=yaml.FullLoader)
                    try:
                        app_targets = app_manifest_data[app_name]['targets'][app_env][app_loc]
                    except:
                        print(colors.FAIL,'Location',app_env,app_loc,'for',app_name,'is not defined',colors.ENDC)
                        continue

                    for target in app_targets:
                        print(colors.UNDERLINE,target.split(':')[0],colors.ENDC)
                        ssh_host = target.split(':')[0]
                        ssh_port = target.split(':')[1]
                        if act_name == 'check':
                            host = target.split(':')[0]
                            healthcheck(
                                host,
                                str(app_manifest_data[app_name]['ports']['http']),
                                str(app_manifest_data[app_name]['healthcheck']['endpoint']),
                                str(app_manifest_data[app_name]['healthcheck']['method']),
                                str(app_manifest_data[app_name]['healthcheck']['response'])
                            )
                        elif act_name in ['start' ,'stop','restart','is-active']:
                            app_state = str(vars_data['acts'][int(a)])
                            ssh_command = "sudo systemctl" + " " + app_state + " " + app_name
                            chstate(ssh_host,ssh_port,ssh_user,ssh_key,str(ssh_command))
                        elif act_name == 'get-version':
                            log_file = app_log_dir + app_name + "/" + app_name + ".log"
                            ssh_command = "sudo tail -n 1" + " " + log_file + "| cut -d ' ' -f 5"
                            version(ssh_host,ssh_port,ssh_user,ssh_key,str(ssh_command),app_name)
                        else:
                            print_fail()
                            sys.exit(1)

signal.signal(signal.SIGINT, sigint_handler)
main()
sys.exit(0)