# QR試作用のPIO受信。既定はGP9・9600bps・8N1・PIO0/SM0で、NF55G用UART1を使わない。
# PIOが受信した値を割込みでRAMリングへ移し、通常処理からread()で取り出す。

"""RP2350 QR UART receiver: GP9, 9600 8N1, PIO0/SM0, no UART1 use.

Dedicated test only; caller owns SM0. Sampling timing follows the MicroPython
PIO UART example. No hardware is touched until QRPioRx is constructed.
"""
from machine import Pin, disable_irq, enable_irq
import rp2


@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_RIGHT, fifo_join=rp2.PIO.JOIN_RX)
def _receive():
    label("start")
    wait(0, pin, 0)
    set(x, 7) [10]
    label("bits")
    in_(pins, 1)
    jmp(x_dec, "bits") [6]
    jmp(pin, "stop_ok")
    mov(isr, invert(null))
    push(block)
    irq(rel(0))
    wait(1, pin, 0)
    jmp("start")
    label("stop_ok")
    push(block)
    irq(rel(0))


class QRPioRx:
    def __init__(self, rx_pin=9, baudrate=9600, sm_id=0, tx_idle_pin=8, buffer_size=256):
        if buffer_size < 2 or buffer_size & (buffer_size - 1):
            raise ValueError("buffer_size must be a power of two")
        self._mask = buffer_size - 1
        self._buf = bytearray(buffer_size)
        self._head = 0
        self._tail = 0
        self._fault = 0
        self.rx = Pin(rx_pin, Pin.IN, Pin.PULL_UP)
        # Host RX1 is wired, but this test never sends configuration commands.
        self.tx_idle = (Pin(tx_idle_pin, Pin.OUT, value=1)
                        if tx_idle_pin is not None else None)
        self.sm = rp2.StateMachine(sm_id, _receive, freq=baudrate * 8,
                                   in_base=self.rx, jmp_pin=self.rx)
        self.sm.irq(self._irq, hard=True)
        self.sm.active(1)

    def _irq(self, sm):
        while sm.rx_fifo():
            # Shift inside native get: avoid allocating a large integer in IRQ.
            value = sm.get(None, 24)
            if value == 255:
                self._fault = 1
                continue
            next_head = (self._head + 1) & self._mask
            if next_head == self._tail:
                self._fault = 2
            else:
                self._buf[self._head] = value
                self._head = next_head

    def any(self):
        return (self._head - self._tail) & self._mask

    def read(self, count=1):
        result = bytearray(min(count, self.any()))
        for i in range(len(result)):
            result[i] = self._buf[self._tail]
            self._tail = (self._tail + 1) & self._mask
        return bytes(result)

    # IRQとの競合を避けて異常を回収し、異常があれば残りの受信データも破棄する。
    def take_error(self):
        token = disable_irq()
        fault = self._fault
        self._fault = 0
        if fault:
            self._tail = self._head
        enable_irq(token)
        if fault == 1:
            return "QR_UART_FRAME"
        if fault == 2:
            return "QR_RX_OVERFLOW"
        return None

    def close(self):
        self.sm.active(0)
        self.sm.irq(None)
