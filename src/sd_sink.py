"""FAT SD CSV sink. All methods must run outside NF55G transactions."""

import os

try:
    from .logger import CSV_FIELDS, LoggerError
except ImportError:
    from logger import CSV_FIELDS, LoggerError


def csv_line(values):
    fields = []
    for value in values:
        text = str(value)
        if any(char in text for char in (',', '"', '\r', '\n')):
            text = '"' + text.replace('"', '""') + '"'
        fields.append(text)
    return ','.join(fields) + '\n'


class FileSDSink:
    """Filesystem implementation, also testable with a temporary host folder.

    BANK_A/B are dedicated logger directories. Never adopt a preexisting bank
    without its ownership marker. Rotation removes only logger-shaped CSVs.
    """
    def __init__(self, mount_point="/sd", fs=None, open_file=None, busy=None):
        self.root = mount_point.rstrip('/')
        self.fs = fs or os
        self.open_file = open_file or open
        self.busy = busy or (lambda: False)
        self.status = "MOUNT_ERR"
        self.file = None
        self.open_filename = None
        self.file_bytes = 0
        self.bank = "BANK_A"
        self.bank_bytes = {"BANK_A": 0, "BANK_B": 0}
        self.capacity_bytes = 0
        self.last_error = None

    def _guard(self):
        if self.busy():
            raise LoggerError("COMM_BUSY")

    def _error(self, code, exc):
        self.last_error = repr(exc)
        self.status = "FULL" if getattr(exc, "errno", None) == 28 else code
        raise LoggerError(self.status)

    @staticmethod
    def _log_name(name):
        return (len(name) == 19 and name[8] == '_' and name.endswith('.csv')
                and (name[:8] + name[9:15]).isdigit())

    def _prepare_banks(self):
        for bank in self.bank_bytes:
            path = self.root + '/' + bank
            try:
                self.fs.stat(path)
            except OSError as exc:
                if getattr(exc, 'errno', exc.args[0] if exc.args else None) != 2:
                    raise
                self.fs.mkdir(path)
                with self.open_file(path + '/.nf55_logger', 'w') as marker:
                    marker.write('NF55G logger\n')
            self.fs.stat(path + '/.nf55_logger')
            total = 0
            for name in self.fs.listdir(path):
                if self._log_name(name):
                    total += self.fs.stat(path + '/' + name)[6]
            self.bank_bytes[bank] = total
        self.capacity_bytes = self.usage()['capacity_bytes']
        if self.capacity_bytes <= 0:
            raise OSError('invalid filesystem capacity')
        try:
            with self.open_file(self.root + '/.nf55_active_bank', 'r') as marker:
                active = marker.read().strip()
        except OSError as exc:
            if getattr(exc, 'errno', exc.args[0] if exc.args else None) != 2:
                raise
            if any(self.bank_bytes.values()):
                raise OSError('active bank record missing; preserve existing logs')
            active = 'BANK_A'
            self._save_bank(active)
        if active not in self.bank_bytes:
            raise OSError('invalid active bank record')
        self.bank = active

    def _save_bank(self, bank):
        self._guard()
        pending = self.root + '/.nf55_active_bank.tmp'
        with self.open_file(pending, 'w') as marker:
            marker.write(bank + '\n')
            marker.flush()
        # FAT rename may reject an existing destination. A power loss in this
        # small gap leaves no active marker: mount then refuses to erase logs.
        self._guard()
        try:
            self.fs.remove(self.root + '/.nf55_active_bank')
        except OSError as exc:
            if getattr(exc, 'errno', exc.args[0] if exc.args else None) != 2:
                raise
        self.fs.rename(pending, self.root + '/.nf55_active_bank')

    def mount(self):
        self._guard()
        try:
            self.fs.stat(self.root)
            self._prepare_banks()
            self.status = "OK"
        except OSError as exc:
            self._error("MOUNT_ERR", exc)

    def _rotate_bank(self):
        other = 'BANK_B' if self.bank == 'BANK_A' else 'BANK_A'
        path = self.root + '/' + other
        for name in self.fs.listdir(path):
            self._guard()
            if self._log_name(name):
                self.fs.remove(path + '/' + name)
        self.bank_bytes[other] = 0
        self._save_bank(other)
        self.bank = other

    def open(self, filename):
        self._guard()
        if self.status != 'OK':
            raise LoggerError(self.status)
        if not self._log_name(filename):
            raise LoggerError('FILENAME')
        try:
            if self.bank_bytes[self.bank] >= self.capacity_bytes * 0.45:
                self._rotate_bank()
            path = self.root + '/' + self.bank + '/' + filename
            try:
                self.fs.stat(path)
            except OSError as exc:
                if getattr(exc, 'errno', exc.args[0] if exc.args else None) != 2:
                    raise
            else:
                raise LoggerError('FILE_EXISTS')
            usage = self.usage()
            if usage['used_percent'] >= 90:
                raise LoggerError('FULL')
            self.file = self.open_file(path, 'wb')
            self.open_filename = path
            self.file_bytes = 0
            self._write(csv_line(CSV_FIELDS))
        except OSError as exc:
            self._error('OPEN_ERR', exc)

    def _write(self, text):
        if self.file is None:
            raise LoggerError('OPEN_ERR')
        data = text.encode('utf-8')
        count = self.file.write(data)
        if count is not None and count != len(data):
            raise OSError('short SD write')
        self.file_bytes += len(data)
        self.bank_bytes[self.bank] += len(data)

    def write_record(self, row):
        self._guard()
        if self.status != 'OK':
            raise LoggerError(self.status)
        try:
            if self.usage()['used_percent'] >= 90:
                self.status = 'FULL'
                raise LoggerError('FULL')
            self._write(csv_line(row))
        except OSError as exc:
            self._error('WRITE_ERR', exc)

    def flush(self):
        self._guard()
        try:
            if self.file is not None:
                self.file.flush()
        except OSError as exc:
            self._error('WRITE_ERR', exc)

    def close(self):
        self._guard()
        file, self.file = self.file, None
        try:
            if file is not None:
                file.close()
        except OSError as exc:
            self._error('WRITE_ERR', exc)

    def reinit(self):
        self._guard()
        try:
            self.close()
        except LoggerError:
            pass
        self.mount()

    def usage(self):
        self._guard()
        try:
            stat = self.fs.statvfs(self.root)
            size = stat[1] or stat[0]
            capacity = size * stat[2]
            used = capacity - size * stat[3]
            return dict(capacity_bytes=capacity, used_bytes=used,
                        used_percent=100.0 * used / capacity if capacity else 0.0)
        except OSError as exc:
            self._error('MOUNT_ERR', exc)


class PicoSDSink(FileSDSink):
    def __init__(self, mount_point='/sd', startup_delay_ms=0, cs_before_spi=False, **kwargs):
        super().__init__(mount_point, **kwargs)
        if not isinstance(startup_delay_ms, int) or not 0 <= startup_delay_ms <= 2000:
            raise ValueError('startup_delay_ms must be 0..2000')
        self.startup_delay_ms = startup_delay_ms
        self.cs_before_spi = bool(cs_before_spi)
        self.card = None
        self.mounted = False
        self.mount_stage = 'NOT_STARTED'

    def mount(self):
        self._guard()
        self.last_error = None
        self.mount_stage = 'IMPORT'
        try:
            from machine import Pin, SPI
            try:
                from .sd_card import SDCard
            except ImportError:
                from sd_card import SDCard
            if self.mounted:
                self.mount_stage = 'UNMOUNT'
                self.fs.umount(self.root)
                self.mounted = False
            # Opt-in investigation settings; production defaults stay unchanged.
            if self.startup_delay_ms:
                from .pico_clock import SystemClock
                self.mount_stage = 'STARTUP_WAIT'
                SystemClock().sleep_ms(self.startup_delay_ms)
            cs = None
            if self.cs_before_spi:
                self.mount_stage = 'CS_SETUP'
                cs = Pin(17, Pin.OUT, value=1)
            self.mount_stage = 'SPI_SETUP'
            # MISO with internal pullup for reliable signal (ADA-5703 requirement)
            miso = Pin(16, Pin.IN, Pin.PULL_UP)
            spi = SPI(0, sck=Pin(18), mosi=Pin(19), miso=miso)
            self.mount_stage = 'CARD_INIT'
            self.card = SDCard(spi, cs if cs is not None else Pin(17))
            self.mount_stage = 'VFS_MOUNT'
            try:
                from vfs import VfsFat, mount
            except ImportError:
                VfsFat, mount = self.fs.VfsFat, self.fs.mount
            mount(VfsFat(self.card), self.root)
            self.mounted = True
            self.mount_stage = 'BANK_SETUP'
            super().mount()
            self.mount_stage = 'READY'
        except OSError as exc:
            self._error('MOUNT_ERR', exc)
