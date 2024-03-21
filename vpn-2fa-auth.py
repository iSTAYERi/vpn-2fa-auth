import sys
import pyotp
import subprocess
import pexpect


# get the passwords from password manager ('pass' in my case)
def get_password(account):
    try:
        # Execute 'pass' cli utility and get the password. This utility use GUI root password request.
        _password = subprocess.check_output(["pass", account]).decode().strip()
        return _password
    except subprocess.CalledProcessError as e:
        print(f"Password get error: {e}")
        return None


def connect_to_vpn_openconnect(username, password1, root_passwd, _totp, _vpn_server_name):
    try:
        child = pexpect.spawn(f"sudo openconnect {_vpn_server_name}")
        # Uncomment for logs output. Warning: passwords output in open state
        # child.logfile = sys.stdout.buffer

        child.expect_exact("[sudo] password for username: ")
        child.sendline(root_passwd)

        child.expect_exact("Username:")
        child.sendline(username)

        child.expect_exact("Password:")
        child.sendline(password1)

        totp_code = _totp.now()
        child.expect_exact("Password:")
        child.sendline(totp_code)

        child.expect("200 OK")
        print("VNP connection successful")
        child.wait()
    except pexpect.exceptions.EOF:
        print("Error: unknown error")
    except pexpect.exceptions.TIMEOUT:
        print("Error: process timeout")


def connect_to_vpn_nm(username, password1, root_passwd, _totp, _vpn_name):
    try:
        child = pexpect.spawn(f"sudo nmcli connection up id \"{_vpn_name}\" --ask ")
        # Uncomment for logs output. Warning: passwords output in open state
        # child.logfile = sys.stdout.buffer

        child.expect_exact("[sudo] password for username: ")
        child.sendline(root_passwd)

        child.expect_exact("Username:")
        child.sendline(username)

        child.expect_exact("Password:")
        child.sendline(password1)

        totp_code = _totp.now()
        child.expect_exact("Password:")
        child.sendline(totp_code)

        child.expect(pexpect.EOF)
        print("VNP connection successful")
    except pexpect.exceptions.EOF:
        print("Error: unknown error")
    except pexpect.exceptions.TIMEOUT:
        print("Error: process timeout")


login = "username"  # username for vpn connection
password = get_password("vpn_pass")  # get the password for vpn connection
secret = get_password("vpn_secret")  # get the secret key of your TOTP auth
root = get_password("sudo")  # get the sudo password
totp = pyotp.TOTP(secret)
vpn_name = "SOME NAME"  # name of your VPN connection in network manager
vpn_server_name = "some.server.com"  # server name of your VPN. Use for openconnect only

connect_to_vpn_nm(login, password, root, totp, vpn_name)
# Uncomment below if you use openconnect
# connect_to_vpn_openconnect(login, password, root, totp, vpn_server_name)
