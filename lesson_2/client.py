"""Программа-клиент"""

import sys
import json
import socket
import time
import argparse
import logging
import threading
from lesson_2.common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS, ACTION, \
    TIME, USER, ACCOUNT_NAME, SENDER, PRESENCE, RESPONSE, \
    ERROR, MESSAGE, MESSAGE_TEXT, DESTINATION, EXIT
from lesson_2.common.utils import get_message, send_message
from errors import IncorrectDataRecivedError
from decos import log
from metaclass import ClientVerifier
# Инициализация клиентского логера
LOGGER = logging.getLogger('client')


class Client(metaclass=ClientVerifier):

    def __init__(self):
        self.client_name = 'Guest'
        self.server_address = None
        self.server_port = None
        self.presenses = None
        self.server_answer = None
        self.message = None
        self.answer = None

    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_server(self, transport):
        transport.connect((self.server_address, self.server_port))

    @log
    def create_exit_message(self):
        """Функция создаёт словарь с сообщением о выходе"""

        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.client_name
        }

    @log
    def message_from_server(self, sock, my_username):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            try:
                message = get_message(sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == my_username:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                f'\n{message[MESSAGE_TEXT]}')
                else:
                    LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                LOGGER.critical(f'Потеряно соединение с сервером.')
                break

    @log
    def create_message(self, sock, account_name):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        :param sock:
        :param account_name:
        :return:
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(sock, message_dict)
            LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except:
            LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    @log
    def user_interactive(self, sock, username):
        """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message(sock, username)
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                send_message(sock, self.create_exit_message(username))
                print('Завершение соединения.')
                LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    @log
    def create_presence(self):
        """Функция генерирует запрос о присутствии клиента"""
        self.presenses = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name
            }
        }
        LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.client_name}')

    @log
    def process_response_ans(self, message):
        """
        Функция разбирает ответ сервера на сообщение о присутствии,
        возращает 200 если все ОК или генерирует исключение при ошибке
        :param message:
        :return:
        """
        try:
            LOGGER.debug(f'Разбор приветственного сообщения от сервера: {message}')
            if RESPONSE in message:
                if message[RESPONSE] == 200:
                    self.answer = '200 : OK'
                elif message[RESPONSE] == 400:
                    self.answer = f'400 : {message[ERROR]}'
        except ValueError:
            print(f'Неверный ответ сервера - {message}')

    def print_help(self):
        """Функция выводящяя справку по использованию"""

        print(f'Текущий клиен: {self.client_name}')
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    @log
    def arg_parser(self):
        """Парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        self.server_address = namespace.addr
        self.server_port = namespace.port
        self.client_name = namespace.name

        # проверим подходящий номер порта
        if not 1023 < self.server_port < 65536:
            LOGGER.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {self.server_port}. '
                f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
            sys.exit(1)


def main():
    client = Client()
    client.arg_parser()
    if not client.client_name:
        client.client_name = input('Введите имя пользователя: ')

    LOGGER.info(
        f'Запущен клиент с парамертами: адрес сервера: {client.server_address}, '
        f'порт: {client.server_port}, имя пользователя: {client.client_name}')

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport_cl = client.transport
        client.connect_to_server(transport_cl)
        client.create_presence()
        send_message(transport_cl, client.presenses)
        client.process_response_ans(get_message(transport_cl))
        LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {client.answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        LOGGER.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)

    except (ConnectionRefusedError, ConnectionError):
        LOGGER.critical(
            f'Не удалось подключиться к серверу {client.server_address}:{client.server_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # Если соединение с сервером установлено корректно,
        # запускаем клиенский процесс приёма сообщний
        receiver = threading.Thread(target=client.message_from_server, args=(transport_cl, client.client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=client.user_interactive, args=(transport_cl, client.client_name))
        user_interface.daemon = True
        user_interface.start()
        LOGGER.debug('Запущены процессы приема и передачи сообщений')

        # Watchdog основной цикл, если один из потоков завершён,
        # то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках,
        # достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
