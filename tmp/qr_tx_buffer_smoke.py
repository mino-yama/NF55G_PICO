import sys
sys.modules.pop("pico_qr_receive_test", None)
from pico_qr_receive_test import run
class Ate:
    def __init__(self):
        self.rx = b"QR_STATUS?\r\n"
        self.tx = b""
    def any(self): return len(self.rx)
    def read(self, n):
        data, self.rx = self.rx[:n], self.rx[n:]
        return data
    def write(self, data):
        self.tx += data[:2]
        return min(2, len(data))
class Qr:
    def any(self):
        if ate.tx == b"IDLE\r\n": raise KeyboardInterrupt
        return 0
ate = Ate()
result = run(ate, Qr())
assert ate.tx == b"IDLE\r\n"
print("ATE_PARTIAL_TX_PICO_OK", repr(ate.tx))
