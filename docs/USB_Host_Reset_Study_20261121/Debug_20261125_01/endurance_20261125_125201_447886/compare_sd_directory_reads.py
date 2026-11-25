"""Compare FAT directory read time without changing the card or firmware."""

import binascii
import gc
import hashlib
import machine
import os
import sys

assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
logger = app.logger
assert not logger.active and not logger.test_running and not logger.recovery_pending
assert logger.last_test_id == 'T000320' and not app._comm_busy()
sink = logger.sd_sink

def directory_summary(list_entries, file_size):
    started = app.clock.ticks_ms()
    digest = hashlib.sha256()
    files = total_bytes = 0
    for bank in sink.bank_bytes:
        folder = sink.root + '/' + bank
        for entry in list_entries(folder):
            name = entry[0] if isinstance(entry, tuple) else entry
            if sink._log_name(name):
                size = file_size(folder, name, entry)
                digest.update(('{}/{},{}\n'.format(bank, name, size)).encode())
                files += 1
                total_bytes += size
    return (files, total_bytes, binascii.hexlify(digest.digest()).decode(),
            app.clock.ticks_ms() - started)


gc.collect()
streamed = directory_summary(os.ilistdir, lambda folder, name, entry: entry[3])
print('ILISTDIR', streamed)
gc.collect()
original = directory_summary(os.listdir, lambda folder, name, entry: os.stat(folder + '/' + name)[6])
print('LISTDIR_STAT', original)
assert streamed[:3] == original[:3]
print('DIRECTORY_ENTRIES_MATCH')
