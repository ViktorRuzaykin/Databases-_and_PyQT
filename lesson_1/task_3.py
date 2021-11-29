import subprocess
import ipaddress
import socket
import os
from tabulate import tabulate


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


def host_range_ping_tab(network):
    table = [('Доступные', 'Недоступные')]
    sort = [[], []]
    try:
        hosts = list(map(str, ipaddress.ip_network(network).hosts()))
    except ValueError as e:
        print(e)
    else:
        result = host_ping(hosts)
        for host in result:
            if len(host[0]) == 8:
                sort[0].append(f'{host[1].ljust(15)} {host[2]}')
            else:
                sort[1].append(f'{host[1].ljust(15)} {host[2]}')
        table.extend(list(zip(*sort)))
        if len(sort[0]) > len(sort[1]):
            for item in sort[0][len(sort[1]):]:
                table.append((item, None))
        elif len(sort[0]) < len(sort[1]):
            for item in sort[1][len(sort[0]):]:
                table.append((None, item))
        print(tabulate(table, headers='firstrow', stralign='center',
                       tablefmt='pipe'))


host_range_ping_tab('173.194.222.0/28')
