from libfptr10 import IFptr
import logging

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
        self.fptr = IFptr("")
        logger.info("Создание инстанса для работы с кассами Атол")
        self.__port = str(com_port)
        logger.info(f"Выбран порт для связи с ККТ - {com_port}")
        self.__isOpened = 0
        self.__shift_dateTime = ""
        self.__shift_number = 0
        self.__shift_state = 0

    def open_session(self):
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

    def close_session(self):
        """Закрытие сесии с кассой Атол
        """
        self.fptr.close()
        self.__isOpened = self.fptr.isOpened()
        return self.__isOpened

    def get_shift_status(self):
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

    def shift_open(self):
        """Открытие смены на ККТ
        """
        self.fptr.openShift()

    def shift_close(self):
        """Закрытие смены на ККТ и
        печать Z-отчета
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE,
                           IFptr.LIBFPTR_RT_CLOSE_SHIFT)
        self.fptr.report()

    def status_sesson(self):
        """проверка активной сессии с ккт

        Returns:
            [int]: 0-закрыта, 1 - открыта
        """
        self.__isOpened = self.fptr.isOpened()
        return self.__isOpened

    def none_fiscal_print(self, text: str):
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

    def copy_check_print(self, Nfn: int):
        """Повторная печать копии чека

        Args:
            Nfn (int): номер фискального документа для повторной печати
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE,
                           IFptr.LIBFPTR_RT_FN_DOC_BY_NUMBER)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER,
                           int(Nfn))  # указыавется номер документа
        self.fptr.report()

    def pay(self,
            goods: list,
            electronical_pay: bool,
            tax: int,
            client_phone: str,
            taxation: int,
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
            taxation (int): тип системы налогообложения
            tax (int): налоговая ставка
            client_phone (str): телефон покупателя
        """
        __error = False
        # чек прихода
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE,
                           IFptr.LIBFPTR_RT_SELL)  
        self.fptr.setParam(1008, str(client_phone))
        # электронный чек
        if isPrint:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY,
                               False)
        else:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY,
                               True)            
        # выбор системы налогообложения
        if taxation == 0:
            __taxation = IFptr.LIBFPTR_TT_OSN
        elif taxation == 1:
            __taxation = IFptr.LIBFPTR_TT_USN_INCOME
        elif taxation == 2:
            __taxation = IFptr.LIBFPTR_TT_USN_INCOME_OUTCOME
        elif taxation == 3:
            __taxation = IFptr.LLIBFPTR_TT_ESN
        elif taxation == 4:
            __taxation = IFptr.LIBFPTR_TT_PATENT
        else:
            __taxation = IFptr.LIBFPTR_TT_OSN
        # выбор налоговой ставки
        if tax == 0:
            __tax = IFptr.LIBFPTR_TAX_VAT0
        elif tax == 10:
            __tax = IFptr.LIBFPTR_TAX_VAT10
        elif tax == 20:
            __tax = IFptr.LIBFPTR_TAX_VAT20
        elif tax == 110:
            __tax = IFptr.LIBFPTR_TAX_VAT110
        elif tax == 120:
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


if __name__ == "__main__":
    atol = Atol("com3")
    print(atol.open_session())
    # print(atol.status_sesson())
    # atol.shift_close()
    print("статус смены", atol.get_shift_status())
    print(atol.pay([{'name': "test1", 'price': 10.1, 'quantity': 5}],
                   electronical_pay=False,
                   tax=10,
                   taxation=1,
                   client_phone="12345678900",
                   isPrint=False))

    atol.close_session()
