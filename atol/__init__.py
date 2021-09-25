from atol.api_atol import Atol
from ReadSetting import readSetting

(_, _, __port) = readSetting()
atol =Atol(__port)