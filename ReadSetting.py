import configparser
from os.path import abspath, join
import platform


def readSetting():
    """Чтение конфигурации из файла настроек
    """
    OS_NAME = platform.system()
    __path = abspath(__file__)
    if OS_NAME == "Windows":
        __pathToFile = __path[:__path.rfind("\\")]
    else:
        __pathToFile = __path[:__path.rfind("/")]
    #__pathSetting = join(__pathToFile, "Setting.ini")
    __pathSetting = "Setting.ini"
    config = configparser.ConfigParser()
    config.read(__pathSetting, encoding="cp1251")
    __easy_port = int(config.get("EASY", "port"))
    __Easy_ip = str(config.get("EASY", "IP"))
    __kkt_port = str(config.get("KKT", "port"))
    return (__easy_port, __Easy_ip, __kkt_port)


if __name__ == "__main__":
    print(readSetting())
