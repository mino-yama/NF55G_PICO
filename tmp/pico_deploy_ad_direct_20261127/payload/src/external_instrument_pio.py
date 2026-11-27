# 外部測定器Host用の独立PIO UART。PIO1 SM4/5、GP12 TX/GP13 RX、115200/8N1。
# FIFO空き分だけを投入し、受信IRQはRAMリングへ退避する。生成時以外はGPIOへ触れない。
from machine import Pin, disable_irq, enable_irq
import rp2


@rp2.asm_pio(out_init=rp2.PIO.OUT_HIGH, sideset_init=rp2.PIO.OUT_HIGH,
             out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def _transmit():
    pull(block).side(1) [7]
    set(x, 7).side(0) [7]
    label('bits')
    out(pins, 1) [6]
    jmp(x_dec, 'bits')


@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_RX)
def _receive():
    label('start')
    wait(0, pin, 0)
    set(x, 7) [10]
    label('bits')
    in_(pins, 1)
    jmp(x_dec, 'bits') [6]
    jmp(pin, 'stop_ok')
    mov(isr, invert(null))
    push(block)
    irq(rel(0))
    wait(1, pin, 0)
    jmp('start')
    label('stop_ok')
    push(block)
    irq(rel(0))


class ExternalPioUART:
    def __init__(self, buffer_size=2048):
        if buffer_size < 2 or buffer_size & (buffer_size - 1):
            raise ValueError('buffer_size must be a power of two')
        self.tx = rp2.StateMachine(4)
        self.rx = rp2.StateMachine(5)
        if self.tx.active() or self.rx.active():
            raise RuntimeError('external relay PIO state machine already active')
        self._buffer = bytearray(buffer_size)
        self._mask = buffer_size - 1
        self._head = self._tail = self._fault = 0
        self._closed = False
        tx_pin = Pin(12, Pin.OUT, value=1)
        rx_pin = Pin(13, Pin.IN, Pin.PULL_UP)
        try:
            self.tx.init(_transmit, freq=115200 * 8, out_base=tx_pin, sideset_base=tx_pin)
            self.rx.init(_receive, freq=115200 * 8, in_base=rx_pin, jmp_pin=rx_pin)
            self.rx.irq(self._irq, hard=True)
            self.tx.active(1)
            self.rx.active(1)
        except Exception:
            self.tx.active(0)
            self.rx.active(0)
            self.rx.irq(None)
            raise

    def _irq(self, sm):
        while sm.rx_fifo():
            value = sm.get(None, 24)
            # X1リンクはASCIIのみ。0xFFは不正stopのsentinelとも区別不要で拒否する。
            if value > 127:
                self._fault = 1
                continue
            next_head = (self._head + 1) & self._mask
            if next_head == self._tail:
                self._fault = 2
            else:
                self._buffer[self._head] = value
                self._head = next_head

    def any(self):
        return (self._head - self._tail) & self._mask

    def read(self, size=64):
        result = bytearray(min(size, self.any()))
        for index in range(len(result)):
            result[index] = self._buffer[self._tail]
            self._tail = (self._tail + 1) & self._mask
        return bytes(result)

    def write(self, data):
        if self._closed:
            raise OSError('external relay UART closed')
        count = min(len(data), max(0, 4 - self.tx.tx_fifo()))
        for index in range(count):
            self.tx.put(data[index])
        return count

    def take_error(self):
        token = disable_irq()
        fault = self._fault
        self._fault = 0
        if fault:
            self._tail = self._head
        enable_irq(token)
        return 'UART_FRAME' if fault == 1 else 'RX_OVERFLOW' if fault == 2 else None

    def close(self):
        self.tx.active(0)
        self.rx.active(0)
        self.rx.irq(None)
        self._closed = True
