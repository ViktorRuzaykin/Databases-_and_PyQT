

def verifier_socket(list_key_value, name):
    flag_socket = False
    for key, value in list_key_value:
        if 'socket' in str(value):
            flag_socket = True
            if 'AF_INET' not in str(value):
                raise TypeError(f'В классе {name} соткет подключается не по "AF_INET".')
    if not flag_socket:
        raise TypeError(f'В классе {name} нет создания сокета.')


class ClientVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        verifier_socket(clsdict.items(), clsname)
        type.__init__(self, clsname, bases, clsdict)


class ServerVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        verifier_socket(clsdict.items(), clsname)
        type.__init__(self, clsname, bases, clsdict)
