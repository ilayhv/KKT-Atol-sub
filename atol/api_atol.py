from atol.libfptr10 import IFptr
import logging
import queue
from functools import reduce
import datetime

"""
Интерфейс для сопряжения ПО EASY-server с кассами АТОЛ
"""

logger = logging.getLogger("Атол-API")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s\
    - %(name)s\
    - %(levelname)s\
    - %(message)s')

console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)


class Atol():

    def __init__(self, com_port: str) -> None:
        super().__init__()
        self.fptr = IFptr("")
        logger.info("Создание инстанса для работы с кассами Атол")
        self.__port = str(com_port)
        logger.info(f"Выбран порт для связи с ККТ - {com_port}")
        self.__isOpened = 0
        self.__shift_dateTime = ""
        self.__shift_number = 0
        self.__shift_state = 0
        self.isPaperNearEnd = False
        self.isCoverOpened = False
        self.isPaperPresent = False
        self.queue = queue.Queue()

    def __open_session(self):
        """Открытие сессии с кассой Атол
        Returns:
            [int]: 0-закрыта, 1 - открыта
        """
        settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_COM,
            IFptr.LIBFPTR_SETTING_COM_FILE: self.__port,
            IFptr.LIBFPTR_SETTING_BAUDRATE: IFptr.LIBFPTR_PORT_BR_115200
            }
        self.fptr.setSettings(settings)
        self.fptr.open()
        self.__isOpened = self.fptr.isOpened()
        return self.__isOpened

    def __close_session(self):
        """Закрытие сесии с кассой Атол
        """
        self.fptr.close()
        self.__isOpened = self.fptr.isOpened()
        return self.__isOpened

    def __get_shift_status(self):
        """Получить статус смены,
        открыта, закрыта
        Returns:
            [int]: 0-закрыта, 1 - открыта
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE,
                           IFptr.LIBFPTR_DT_SHIFT_STATE)
        self.fptr.queryData()
        self.__shift_state = self.fptr.getParamInt(
                                    IFptr.LIBFPTR_PARAM_SHIFT_STATE)
        self.__shift_number = self.fptr.getParamInt(
                                    IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
        self.__shift_dateTime = self.fptr.getParamDateTime(
                                    IFptr.LIBFPTR_PARAM_DATE_TIME)
        return self.__shift_state

    def __shift_open(self):
        """Открытие смены на ККТ
        """
        self.fptr.openShift()

    def __shift_close(self):
        """Закрытие смены на ККТ и
        печать Z-отчета
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE,
                           IFptr.LIBFPTR_RT_CLOSE_SHIFT)
        self.fptr.report()

    def __status_sesson(self):
        """проверка активной сессии с ккт

        Returns:
            [int]: 0-закрыта, 1 - открыта
        """
        self.__isOpened = self.fptr.isOpened()
        return self.__isOpened

    def __none_fiscal_print(self, text: str):
        """печать не фискального документа

        Args:
            text (str): текст для печати, для многострочной печати
            строки необходимо отделять друг от друга, разделителем
            \r
        """
        self.fptr.beginNonfiscalDocument()
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TEXT, str(text))
        self.fptr.printText()
        self.fptr.endNonfiscalDocument()

    def __copy_check_print(self, Nfn: int):
        """Повторная печать копии чека

        Args:
            Nfn (int): номер фискального документа для повторной печати
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE,
                           IFptr.LIBFPTR_RT_FN_DOC_BY_NUMBER)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER,
                           int(Nfn))  # указыавется номер документа
        self.fptr.report()

    def __pay(self,
              goods: list,
              electronical_pay: bool,
              tax: str,
              taxation: str,
              isPrint=True
              ):
        """ формирование чека для оплаты
        Args:
            goods   (list): список товаров в котором содержатся словари с
                названием товара, стоимостью за еденицу товара и кол-во товара
                пример:
                    [{'name': test1, 'price': 10.1, 'quantity':5},
                     {'name': test2, 'price': 1.3, 'quantity':1}]
            electronical_pay (bool): True - електронный платеж
            isPrint (bool): True - чек печатать
            taxation (str): тип системы налогообложения(osn,usnIncome,
            usnIncomeOutcome,esn,patent)
            tax (str): налоговая ставка (none,vat0,vat10,vat110,vat20)
            client_phone (str): телефон покупателя
        """
        __error = False
        # чек прихода
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                           IFptr.LIBFPTR_RT_SELL)
        # электронный чек
        if isPrint:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY,
                               False)
        else:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY,
                               True)
        # выбор системы налогообложения
        if taxation == "osn":
            __taxation = IFptr.LIBFPTR_TT_OSN
        elif taxation == "usnIncome":
            __taxation = IFptr.LIBFPTR_TT_USN_INCOME
        elif taxation == "usnIncomeOutcome":
            __taxation = IFptr.LIBFPTR_TT_USN_INCOME_OUTCOME
        elif taxation == "esn":
            __taxation = IFptr.LLIBFPTR_TT_ESN
        elif taxation == "patent":
            __taxation = IFptr.LIBFPTR_TT_PATENT
        else:
            __taxation = IFptr.LIBFPTR_TT_OSN
        # выбор налоговой ставки
        if tax == "vat0":
            __tax = IFptr.LIBFPTR_TAX_VAT0
        elif tax == "vat10":
            __tax = IFptr.LIBFPTR_TAX_VAT10
        elif tax == "vat20":
            __tax = IFptr.LIBFPTR_TAX_VAT20
        elif tax == "vat110":
            __tax = IFptr.LIBFPTR_TAX_VAT110
        elif tax == "vat120":
            __tax = IFptr.LIBFPTR_TAX_VAT120
        else:
            __tax = IFptr.LIBFPTR_TAX_NO

        self.fptr.setParam(1055,
                           __taxation)  # система налогообложения
        # открытие чека
        self.fptr.openReceipt()
        # добаваление позиций в чек
        __all_summ = 0
        for element in goods:
            try:
                __name = str(element["name"])
            except Exception as ex:
                __error = True
                logger.info(ex)
            try:
                __price = float(element["price"])
            except Exception as ex:
                __error = True
                logger.info(ex)
            try:
                __quantity = int(element["quantity"])
            except Exception as ex:
                __error = True
                logger.info(ex)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, __name)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, __price)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, __quantity)
            __all_summ = __all_summ + (__price*__quantity)
        # налоговая ставка
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, __tax)
        self.fptr.registration()
        # тип оплаты
        if electronical_pay:
            __pay_type = IFptr.LIBFPTR_PT_ELECTRONICALLY
        else:
            __pay_type = IFptr.LIBFPTR_PT_CASH
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE,
                           __pay_type)

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, __all_summ)
        self.fptr.payment()
        # закрытие чека
        self.fptr.closeReceipt()
        return __error

    def __check_document(self):
        __error = ""
        __checkDocumentClosed = self.fptr.checkDocumentClosed()
        __document_closed = self.fptr.getParamBool(
                        IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED)
        __document_printed = self.fptr.getParamBool(
                        IFptr.LIBFPTR_PARAM_DOCUMENT_PRINTED)

        if __checkDocumentClosed < 0:
            __error = str(self.fptr.errorDescription())
            logger.info("Ошибка закрытия документа"+str(__error))
        if not __document_closed:
            self.fptr.cancelReceipt()
            logger.info("Ошибка закрытия документа, отмена последнего чека")
        if not __document_printed:
            __error = str(self.fptr.errorDescription())
            logger.info("Ошибка печати документа"+str(__error))
        return (__error,
                __checkDocumentClosed,
                __document_closed,
                __document_printed)

    def __get_kkt_status(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE,
                           IFptr.LIBFPTR_DT_STATUS)
        self.fptr.queryData()
        self.isPaperNearEnd = self.fptr.getParamBool(
                                    IFptr.LIBFPTR_PARAM_PAPER_NEAR_END)
        self.isCoverOpened = self.fptr.getParamBool(
                                    IFptr.LIBFPTR_PARAM_COVER_OPENED)
        self.isPaperPresent = self.fptr.getParamBool(
                                    IFptr.LIBFPTR_PARAM_RECEIPT_PAPER_PRESENT)
        return (self.isPaperNearEnd, self.isCoverOpened, self.isPaperPresent)

    def __continue_print(self):
        self.fptr.continuePrint()

    def __print_last_document(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE,
                           IFptr.LIBFPTR_RT_LAST_DOCUMENT)
        self.fptr.report()

    def __get_fn_status(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE,
                           IFptr.LIBFPTR_FNDT_FN_INFO)
        self.fptr.fnQueryData()
        __fnSerial = self.fptr.getParamString(
                            IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
        __fnVersion = self.fptr.getParamString(
                            IFptr.LIBFPTR_PARAM_FN_VERSION)
        __fnExecution = self.fptr.getParamString(
                            IFptr.LIBFPTR_PARAM_FN_EXECUTION)
        return(__fnSerial, __fnVersion, __fnExecution)

    def __get_last_document_data(self):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE,
                           IFptr.LIBFPTR_FNDT_LAST_RECEIPT)
        self.fptr.fnQueryData()
        __documentNumber = self.fptr.getParamInt(
                                    IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
        __fiscalSign = self.fptr.getParamString(
                                    IFptr.LIBFPTR_PARAM_FISCAL_SIGN)
        __dateTime = self.fptr.getParamDateTime(
                                    IFptr.LIBFPTR_PARAM_DATE_TIME)
        __receiptType = self.fptr.getParamInt(
                                    IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
        __receiptSum = self.fptr.getParamDouble(
                                    IFptr.LIBFPTR_PARAM_RECEIPT_SUM)
        return (__documentNumber,
                __fiscalSign,
                str(__dateTime),
                __receiptType,
                __receiptSum)

    def update(self,
               mesg: dict):
        logger.info("Получены данные модулем Атол"+str(mesg))
        return self.__analize(mesg)

    def __analize(self,
                  mesg: str):
        __data = dict(mesg)
        __answer = {}
        __answer["cmd"] = __data["cmd"]
        __answer["ans"] = {"error": ""}
        __answer["status"] = {"error": ""}
        __answer["status"]["document_closed"] = True
        __answer["status"]["checkDocumentClosed"] = 0
        __answer["status"]["document_printed"] = True
        # перед каждым действием проверка статуса
        # и если закрыто то попытка открыть
        self.__status_sesson()
        logger.info(self.__isOpened)
        if self.__isOpened == 0:
            self.__open_session()
        if self.__isOpened == 1:
            # проверка статуса ККТ
            if __data["cmd"] == "getDeviceStatus":
                (__paperEnd, __cover, __paperPresent) = self.__get_kkt_status()
                __answer["ans"]["isCoverOpened"] = __cover
                __answer["ans"]["isPaperNearEnd"] = __paperEnd
                __answer["ans"]["isPaperPresent"] = __paperPresent
            # проверка статуса смены
            elif __data["cmd"] == "getShiftStatus":
                __shift = self.__get_shift_status()
                __answer["ans"]["shift"] = __shift
            # печать прерванного документа
            elif __data["cmd"] == "continuePrint":
                self.__continue_print()
                __answer["ans"]["status"] = {"continuePrint": "ok"}
            # печать документа из ФН по номеру
            elif __data["cmd"] == "printFnDocument":
                __fiscalDocumentNumber = __data["fiscalDocumentNumber"]
                self.__copy_check_print(__fiscalDocumentNumber)
                __answer["ans"]["status"] = "ok"
            # получение статуса ФН
            elif __data["cmd"] == "getFnStatus":
                (__fnSerial,
                 __fnVersion,
                 __fnExecution) = self.__get_fn_status()
                __answer["ans"]["fnSerial"] = __fnSerial
                __answer["ans"]["fnVersion"] = __fnVersion
                __answer["ans"]["fnExecution"] = __fnExecution
            # проверка связи с ОФД
            elif __data["cmd"] == "ofdExchangeStatus":
                pass
            # повторная печать последнего документа
            elif __data["cmd"] == "RepeatPrint":
                self.__print_last_document()
                __answer["ans"]["status"] = "ok"
            # открытие смены
            elif __data["cmd"] == "openShift":
                self.__shift_open()
                __answer["ans"]["status"] = "ok"
            # закрытие смены
            elif __data["cmd"] == "closeShift":
                self.__shift_close()
                __answer["ans"]["status"] = "ok"
            # печать не фискального документа
            elif __data["cmd"] == "PrintText":
                __string = reduce(lambda x, y: x + "\r\n" + y, __data["strings"])
                self.__none_fiscal_print(__string)
                __answer["ans"]["status"] = "ok"
            # оплата
            elif __data["cmd"] == "sell":
                # __operator_name = __data["operator"]["name"]
                # __operator_vatin = __data["operator"]["vatin"]
                __taxationType = __data["taxationType"]
                # __paymentsPlace = __data["paymentsPlace"]
                __isPrint = not(__data["electronically"])
                __electronical_pay = True if __data["payments"][0]["type"] == "electronically" else False
                __tax = str(__data["items"][0]["tax"]["type"])
                __goods = []
                for element in __data["items"]:
                    boof = {}
                    boof["name"] = element["name"]
                    boof["price"] = element["price"]
                    boof["quantity"] = element["quantity"]
                    __goods.append(boof)
                self.__pay(__goods,
                           __electronical_pay,
                           __tax,
                           __taxationType,
                           __isPrint)
            (__documentNumber,
             __fiscalSign,
             __dateTime,
             __receiptType,
             __receiptSum) = self.__get_last_document_data()
            __answer["ans"]["__fiscalSign"] = __fiscalSign
            __answer["ans"]["__documentNumber"] = __documentNumber
            __answer["ans"]["__dateTime"] = __dateTime
            __answer["ans"]["__receiptType"] = __receiptType
            __answer["ans"]["__receiptSum"] = __receiptSum
            logger.info("Ответ от модуля Атол"+str(__data))
            (__error,
             __checkDocumentClosed,
             __document_closed,
             __document_printed) = self.__check_document()
            __answer["status"]["error"] = __error
            __answer["status"]["document_closed"] = __document_closed
            __answer["status"]["checkDocumentClosed"] = __checkDocumentClosed
            __answer["status"]["document_printed"] = __document_printed
        else:
            __answer["ans"]["error"] = "No link"
        return __answer
