# 分割到着するATE入力をCR/LFで区切り、実行待ちQueueへ格納する。
# CRLFのLFと空行は無視する。CR待ちを残さず、定期CRでSD処理を妨げない。
# 受信処理だけではコマンドを実行せず、応答の未送信部分も保持する。

"""Bounded CR/LF ATE receiver with CRLF replies; pumping never executes commands."""


class ATEServer:
    def __init__(self, transport, max_line=512, max_pending=8):
        self.transport = transport
        self.max_line = max_line
        self.max_pending = max_pending
        self.pending = []
        self.line = bytearray()
        self.error = None
        self.tx = b''

    def pump(self, budget=64):
        for _ in range(budget):
            if len(self.pending) >= self.max_pending or not self.transport.any():
                break
            raw = self.transport.read(1)
            if not raw:
                break
            value = raw[0]
            if value in (13, 10):
                if self.line or self.error:
                    self.pending.append((bytes(self.line), self.error))
                self.line = bytearray()
                self.error = None
            elif value < 32 or value > 126:
                self.error = 'ASCII' if value > 126 else 'FRAME'
            elif not self.error:
                if len(self.line) >= self.max_line:
                    self.error = 'LINE_TOO_LONG'
                    self.line = bytearray()
                else:
                    self.line.append(value)

    def reply(self, text):
        if self.tx:
            raise RuntimeError('pending ATE response')
        self.tx = (text + '\r\n').encode('ascii')

    # UARTが一部だけ受理した場合は、未送信の末尾を次の巡回へ持ち越す。
    def flush_reply(self):
        if self.tx:
            written = self.transport.write(self.tx)
            if written is not None and written > 0:
                self.tx = self.tx[written:]

    def has_work(self):
        return bool(self.pending or self.line or self.error or self.tx or self.transport.any())
