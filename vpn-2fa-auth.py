import sys
import os
import pyotp
import subprocess
import pexpect
import re


# get the passwords from password manager ('pass' in my case)
def get_password(account):
    try:
        # Execute 'pass' cli utility and get the password. This utility use GUI root password request.
        _password = subprocess.check_output(["pass", account]).decode().strip()
        return _password
    except subprocess.CalledProcessError as e:
        print(f"Password get error for '{account}': {e}")
        return None


def connect_to_vpn_openconnect(username, password1, root_passwd, _totp, _vpn_server_name):
    timeout = int(os.environ.get("VPN_TIMEOUT", "30"))
    try:
        print(f"Starting openconnect to '{_vpn_server_name}'")
        env = os.environ.copy()
        env.update({"LC_ALL": "C", "LANG": "C"})
        child = pexpect.spawn(f"sudo -S -p '' openconnect {_vpn_server_name}", encoding="utf-8", env=env)
        # send sudo password via stdin (-S)
        child.sendline(root_passwd)

        user_prompt_patterns = [
            "Username:",
            "Имя пользователя:",
        ]
        child.expect(user_prompt_patterns, timeout=timeout)
        child.sendline(username)

        pass_prompt_patterns = [
            "Password:",
            "Пароль:",
        ]
        child.expect(pass_prompt_patterns, timeout=timeout)
        child.sendline(password1)

        totp_code = _totp.now()
        child.expect(pass_prompt_patterns, timeout=timeout)
        child.sendline(totp_code)

        child.expect("200 OK", timeout=timeout)
        print("VNP connection successful (openconnect)")
        child.wait()
    except pexpect.exceptions.TIMEOUT as e:
        print(f"Timeout: {e}")
    except pexpect.exceptions.EOF as e:
        print(f"EOF/unknown. Buffer: {getattr(e, 'value', '')}")


def connect_to_vpn_nm(username, password1, root_passwd, _totp, _vpn_name):
    timeout = int(os.environ.get("VPN_TIMEOUT", "30"))
    try:
        print(f"Starting nmcli to connect '{_vpn_name}'")
        env = os.environ.copy()
        env.update({"LC_ALL": "C", "LANG": "C"})
        child = pexpect.spawn(f"sudo -S -p '' nmcli connection up id \"{_vpn_name}\" --ask ", encoding="utf-8", env=env)
        # send sudo password via stdin (-S)
        child.sendline(root_passwd)

        user_prompt_patterns = [
            "Username:",
            "Имя пользователя:",
        ]
        child.expect(user_prompt_patterns, timeout=timeout)
        child.sendline(username)

        pass_prompt_patterns = [
            "Password:",
            "Пароль:",
        ]
        child.expect(pass_prompt_patterns, timeout=timeout)
        child.sendline(password1)

        totp_code = _totp.now()
        child.expect(pass_prompt_patterns, timeout=timeout)
        child.sendline(totp_code)

        child.expect(pexpect.EOF, timeout=timeout)
        print("VNP connection successful (nmcli)")
    except pexpect.exceptions.TIMEOUT as e:
        print(f"Timeout: {e}")
    except pexpect.exceptions.EOF as e:
        print(f"EOF/unknown. Buffer: {getattr(e, 'value', '')}")


login = "sv.bogdanov"  # username for vpn connection
password = get_password("vpn_citrix_pass")  # get the password for vpn connection
secret = get_password("vpn_citrix_secret")  # get the secret key of your TOTP auth
root = get_password("root")  # get the sudo password

if not all([login, password, secret, root]):
    print("Missing required creds (login/password/secret/root). Check pass store")
    sys.exit(1)

totp = pyotp.TOTP(secret)
vpn_name = "DOM RF"  # name of your VPN connection in network manager
vpn_server_name = "vpn.domrfbank.ru"  # server name of your VPN.

connect_to_vpn_nm(login, password, root, totp, vpn_name)
# Uncomment below if you use openconnect
# connect_to_vpn_openconnect(login, password, root, totp, vpn_server_name)
