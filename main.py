from atol import atol
from kkt_server import easy
import time

easy.attach(atol)

while True:
    time.sleep(10)