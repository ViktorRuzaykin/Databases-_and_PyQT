import subprocess
import ipaddress
import socket
import os


def ip_address(host):
    try:
        if type(host) in (str, int):
            check = str(ipaddress.ip_address(host))
        else:
            return False
    except ValueError:
        try:
            check = socket.gethostbyname(host)
        except socket.gaierror:
            return False
    return check


def host_ping(lst):
    result = []
    for host in lst:
        verified_ip = ip_address(host)
        if verified_ip:
            with open(os.devnull, 'w') as DNULL:
                response = subprocess.call(
                    ["ping", "-n", "2", "-w", "2", verified_ip], stdout=DNULL
                )
            if response == 0:
                result.append(('Доступен', str(host), f'[{verified_ip}]'))
                continue
        result.append(('Не доступен', str(host),
                       f'[{verified_ip if verified_ip else "Не определён"}]'))

    return result


def host_range_ping(network):
    try:
        hosts = list(map(str, ipaddress.ip_network(network).hosts()))
    except ValueError as e:
        print(e)
    else:
        count = 255
        for host in host_ping(hosts):
            if not count:
                break
            count -= 1
            print(f'{host[0].ljust(11)} {host[1].ljust(15)} {host[2]}')


host_range_ping('173.194.222.0/28')
