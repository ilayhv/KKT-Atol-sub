import socket
import select
import json
import time
import logging
import struct
import queue
from threading import Thread
import platform


# настройка логера
logger = logging.getLogger("Easy-API")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s\
    - %(name)s\
    - %(levelname)s\
    - %(message)s')

console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)


class EasyKktServer(Thread):
    def __init__(self, host="127.0.0.1", port="5555") -> None:
        super().__init__()
        logger.info(f"Создание инстанса класса Easy-API")

        self.WAIT_TIME = 5
        self.HOST = host
        self.PORT = port
        self.OS_NAME = platform.system()

    def __send(self,
               sock: socket.socket,
               data: dict):
        __mesg = str(data).encode()
        __l = str(len(__mesg)).encode().ljust(4)
        try:
            sock.send(__l+__mesg)
        except Exception as ex:
            logger.info("Ошибка отправки данных")
            logger.info(ex)
            self.__close_connection(sock)

    def __resiver(self,
                  sock: socket.socket):
        __data = {}
        try:
            __recv = sock.recv(4)
            __lenMsg, = struct.unpack(">L", __recv)
            __recv = sock.recv(__lenMsg)
            #  recv=sockLS.recv(2048)
            try:
                __data = json.loads(__recv.decode("utf-8"))
            except Exception as ex:
                logger.info("Ошибка распаковки данных в utf-8")
                logger.info(ex)
                logger.info(str(__recv))
                try:
                    logger.info("Смена кодировки на cp1251 и попытка распаковки данных")
                    __data = json.loads(__recv.decode("cp1251"))
                except Exception as ex:
                    logger.info("Ошибка распаковки данных")
                    logger.info(ex)
                    logger.info(str(__recv))
        except Exception as ex:
            logger.info("Ошибка чтения данных")
            logger.info(ex)
            self.__close_connection(sock)
        return __data

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as __sock:
            __sock.bind(('', self.PORT))
            __sock.listen(5)
            self.__sockets = [__sock]  # список сокетов зарегистрированных
            self.__message_queues = {}  # Очередь сообщений
            logger.info("Начало работы")
            while True:
                (__readable,
                 __writable,
                 __exceptional) = select.select(self.__sockets,
                                                self.__sockets,
                                                self.__sockets,
                                                1)
                # Закрываем сбойные сокеты
                for __ex_sock in __exceptional:
                    self.__close_connection(__ex_sock)
                # Для каждого сокета готового к записи
                for __wr_sock in __writable:
                    if self.__message_queues[__wr_sock].qsize() != 0:
                        try:
                            next_msg = self.__message_queues[__wr_sock].get()
                            self.__send(__wr_sock, next_msg)
                        except queue.Empty:
                            pass
                        except KeyError:
                            pass
                    else:
                        time.sleep(0.1)
                for __read_sock in __readable:
                    if __read_sock is __sock:
                        try:
                            (__connection,
                             __client_address) = __read_sock.accept()
                            logger.info("Готовность принять новое подключение")
                            logger.info(__client_address)
                            __connection.setblocking(0)
                            logger.info("Добавление сокета в список советов")
                            self.__sockets.append(__connection)
                            logger.info("Создание очереди сообщений")
                            self.__message_queues[__connection] = queue.Queue()
                        except:
                            logger.info("попытка соеденения")
                            logger.info(__read_sock)
                            #  close_connection(r,sockets,OS_NAME,message_queues)
                    else:
                        try:
                            __dataRead = self.__resiver(__read_sock)
                            logger.info("Получены данные")
                            logger.info(__dataRead)
                        except Exception as ex:
                            logger.info(ex)
                            self.__close_connection(__dataRead)
                        if __dataRead:
                            print(__dataRead)
                            if len(__dataRead) == 0:
                                self.__close_connection(__read_sock)
                            else:
                                print("отправка в атол",__dataRead)
                                __atol_answer = self.atol.update(__dataRead)
                                print("ответ атол",__atol_answer)
                                for __q_sock in self.__message_queues:
                                    if __q_sock == __read_sock:
                                        self.__message_queues[__q_sock].put(__atol_answer)
                        else:
                            self.__close_connection(__read_sock)
                            logging.info(time.ctime()+"Клиент отвалился")

    def __close_connection(self,
                           sock: socket.socket):
        try:
            self.__sockets.remove(sock)
        except:
            pass
        if sock in self.__message_queues:
            del self.__message_queues[sock]

        if self.OS_NAME == 'Linux':
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception as ex:
                logger.info(ex)
        try:
            sock.close()
        except Exception as ex:
            logger.info(ex)


    def attach(self,
               atol):
        self.atol = atol

    def detach(self):
        self.atol = None
