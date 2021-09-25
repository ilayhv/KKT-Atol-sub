from kkt_server.easy_api import EasyKktServer
from ReadSetting import readSetting

(__port, __host, _) = readSetting()

easy = EasyKktServer(host=__host,
                     port=__port)

easy.setDaemon(True)
easy.start()
