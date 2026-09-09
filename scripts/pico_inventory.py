"""Read-only Pico inventory; execute in RAM with mpremote resume run.

Does not import deployed application modules or initialize UART/I2C/SPI.
The host must select the intended USB serial port. REPL entry interrupts any
running application; resume avoids mpremote's automatic soft reset.
"""

import os
import sys
import machine
import hashlib
import binascii


def inventory(path, depth=0):
    for name in sorted(os.listdir(path)):
        full = path.rstrip("/") + "/" + name
        info = os.stat(full)
        if info[0] & 0x4000:
            print("DIR|" + full)
            if full not in ("/sd", "/sdcard") and depth < 4:
                inventory(full, depth + 1)
        else:
            print("FILE|{}|{}".format(full, info[6]))
            if full.endswith((".py", ".mpy")):
                digest = hashlib.sha256()
                with open(full, "rb") as source:
                    while True:
                        chunk = source.read(512)
                        if not chunk:
                            break
                        digest.update(chunk)
                print("SHA256|{}|{}".format(full, binascii.hexlify(digest.digest()).decode()))
            if full in ("/boot.py", "/main.py") and info[6] <= 16384:
                print("BOOT_SOURCE_BEGIN|" + full)
                with open(full) as source:
                    print(source.read())
                print("BOOT_SOURCE_END|" + full)


print("PICO_INVENTORY_BEGIN")
print("IMPLEMENTATION|" + repr(sys.implementation))
print("VERSION|" + sys.version)
print("PLATFORM|" + sys.platform)
print("UNAME|" + repr(os.uname()))
print("UNIQUE_ID|" + binascii.hexlify(machine.unique_id()).decode())
print("FREQ|" + str(machine.freq()))
print("CWD|" + os.getcwd())
print("SYS_PATH|" + repr(sys.path))
inventory("/")
print("PICO_INVENTORY_END")
