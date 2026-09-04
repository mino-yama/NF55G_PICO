from machine import UART, I2C, Pin, RTC
import time

#------------------------------------------------------------
# US76HG PMBus / RS232C-I2C Bridge Program Release Note
# CreateUser : M.Yamada
# CreateDate : 2023/02/02
#
# UpdateUser : M.Yamada
# UpdateDate : 2026/04/23
#------------------------------------------------------------
# Hardware composition
# Host PC (Pseudo HOST)
#   - RS232C cross connection
#
# Controller
#   - Raspberry Pi Pico (MCU: RP2040)
#
# RS232C interface
#   - Waveshare Pico-2CH-RS232
#   - 2-Channel UART to RS232 Module for Raspberry Pi Pico
#   - SP3232EEN Transceiver
#
# I2C level converter
#   - FXMA2102 I2C Bus Level Converter Module
#   - VCCA = +3.3V (Pico side)
#   - VCCB = +5V (Target device side)
#   - OE   = +3.3V
#   - R1, R2 = 4.7kΩ pull-up to +3.3V
#   - R3, R4 = Not mounted
#   - +5V side pull-up resistors are mounted on target device side
#
# Target device
#   - PMBus / I2C device
#   - Device side logic : +5V
#
# Power configuration
#   - Pico side and target device side +5V are separate systems
#   - GND is common
#
# UART / I2C assignment
#   - GP0 : TXD0 / UART0 TX
#   - GP1 : RXD0 / UART0 RX
#   - GP4 : TXD1 / UART1 TX
#   - GP5 : RXD1 / UART1 RX
#   - GP2 : I2C1 SDA
#   - GP3 : I2C1 SCL
#------------------------------------------------------------
# Communication overview
# - This program receives ASCII commands from RS232C,
#   executes PMBus/I2C access, and returns ASCII response.
# - Command end : CR or LF
# - Response end: CR
# - PMBus slave address: 01h (7-bit)
# - PMBus speed       : 100 kbps
# - PEC default       : Enabled
#
# Date / Time overview
# - Pico does not keep date/time after power cycle.
# - Set DATE and TIME from ATE / PC after boot.
# - Log header uses Date/Time after both DATE and TIME are set.
# - If not set, log header uses ticks_ms().
#
# Command list
#  *IDN?
#     Return bridge identification string.
#
#  DATE_YYYYMMDD
#     Set date.
#     Example: DATE_20260325
#
#  TIME_HHMMSS
#     Set time.
#     Example: TIME_143015
#
#  DATE?
#     Read current date.
#     Response example: 20260325
#
#  TIME?
#     Read current time.
#     Response example: 143015
#
#  DATETIME?
#     Read current date and time.
#     Response example: 20260325_143015
#
#  STATUS?
#     Read STATUS_MFR_SPECIFIC(80h) and return all 8 bits.
#
#  STATUS_00? ～ STATUS_07?
#     Read STATUS_MFR_SPECIFIC(80h) and return specified bit only.
#     Bit definition:
#       00 = AC abnormal
#       01 = +12V abnormal
#       02 = +3.3V abnormal
#       03 = +5V abnormal
#       04 = DC fan abnormal
#       05-07 = Reserved
#
#  PAGE?
#     Read PAGE(00h) current value.
#
#  PAGE_02
#     Write PAGE=02h. Select +3.3V side.
#
#  PAGE_03
#     Write PAGE=03h. Select +5V side.
#
#  VOUT5?
#     Set PAGE=03h, execute READ_VOUT(8Bh), return voltage value only.
#     Example response: 5.0100
#
#  VOUT33?
#     Set PAGE=02h, execute READ_VOUT(8Bh), return voltage value only.
#     Example response: 3.3000
#
#  IOUT5?
#     Set PAGE=03h, execute READ_IOUT(8Ch), return current value only.
#     Example response: 18.2500
#
#  IOUT33?
#     Set PAGE=02h, execute READ_IOUT(8Ch), return current value only.
#     Example response: 6.5000
#
#  FW_CTRL?
#     Read firmware version of control MCU by C0h.
#
#  FW_COMM?
#     Read firmware version of communication MCU by C1h.
#
#  ERROR_ALL?
#     Read STATUS, V33, I33, V5, I5 sequentially and return one line.
#     Returned numeric values are unit-less strings for ATE handling.
#
#  PEC_ON
#     Enable PEC append/check.
#
#  PEC_OFF
#     Disable PEC append/check.
#
#  PMB_RW_xx?
#     Execute arbitrary PMBus Read Word command (xx = hex).
#
#  PMB_RB_xx?
#     Execute arbitrary PMBus Read Byte command (xx = hex).
#
#  ANY_WRITE_xx_yy
#     Execute arbitrary 1-byte PMBus write.
#     xx = command(hex), yy = data(hex)
#
#  LOG_INFO?
#     Return current log status.
#     Example: LOG_COUNT=37,LOG_MAX=240,OVERFLOW=0
#
#  LOG_LAST?
#     Return latest log line.
#
#  LOG_IDX_n?
#     Return log line by logical index.
#     0 = oldest, log_count-1 = newest
#     Example: LOG_IDX_0?
#
#  LOG_CLEAR
#     Clear RAM log buffer.
#------------------------------------------------------------

# =========================================================
# UART setting
# =========================================================
UART_BAUD = 57600
UART_BITS = 8
UART_PARITY = None
UART_STOP = 1

# 0: CH0 (GP0/GP1)  /  1: CH1 (GP4/GP5)
ACTIVE_UART_CH = 0

uart0 = UART(
    0,
    baudrate=UART_BAUD,
    bits=UART_BITS,
    parity=UART_PARITY,
    stop=UART_STOP,
    tx=Pin(0),
    rx=Pin(1),
)
uart0.init(UART_BAUD, bits=UART_BITS, parity=UART_PARITY, stop=UART_STOP)

uart1 = UART(
    1,
    baudrate=UART_BAUD,
    bits=UART_BITS,
    parity=UART_PARITY,
    stop=UART_STOP,
    tx=Pin(4),
    rx=Pin(5),
)
uart1.init(UART_BAUD, bits=UART_BITS, parity=UART_PARITY, stop=UART_STOP)

uart = uart0 if ACTIVE_UART_CH == 0 else uart1

# =========================================================
# RTC setting
# =========================================================
rtc = RTC()
rtc_valid = False
pending_date = None   # (year, month, day)
pending_time = None   # (hour, minute, second)

# =========================================================
# I2C / PMBus setting
# =========================================================
I2C_FREQ = 100000
PMBUS_ADDR = 0x01

# GP2=SDA, GP3=SCL
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=I2C_FREQ)

# PMBus command
CMD_PAGE       = 0x00
CMD_STATUS_MFR = 0x80
CMD_READ_VOUT  = 0x8B
CMD_READ_IOUT  = 0x8C
CMD_FW_CTRL    = 0xC0
CMD_FW_COMM    = 0xC1

PAGE_33V = 0x02
PAGE_5V  = 0x03

# PEC enable
PEC_ENABLE = True

# retry count
RETRY_COUNT = 5

# LED
led = Pin(25, Pin.OUT)

# UART receive buffer
rx_buffer = ""
last_blink = time.ticks_ms()

# =========================================================
# RAM log setting
# 32KB fixed ring buffer
# 240 entries x 128 bytes = 30,720 bytes
# Old data is overwritten when full
# =========================================================
LOG_LINE_MAX = 128
LOG_LINE_COUNT = 240

log_storage = bytearray(LOG_LINE_MAX * LOG_LINE_COUNT)
log_lengths = bytearray(LOG_LINE_COUNT)
log_head = 0
log_count = 0
log_overflow = False

# Power stabilization wait
time.sleep_ms(200)

# =========================================================
# RAM log utility
# =========================================================
def _safe_text(obj):
    if isinstance(obj, str):
        return obj
    try:
        return str(obj)
    except Exception:
        return repr(obj)

def get_datetime_string():
    global rtc_valid

    if rtc_valid:
        dt = rtc.datetime()
        # (year, month, day, weekday, hour, minute, second, subseconds)
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            dt[0], dt[1], dt[2], dt[4], dt[5], dt[6]
        )
    else:
        return "{:010d}".format(time.ticks_ms() & 0x3FFFFFFF)

def log_store(tag, text):
    """
    Save log into fixed-length ring buffer and print to Thonny console.
    Format:
      [YYYY-MM-DD hh:mm:ss] TAG text   (after DATE/TIME set)
      [0000123456] TAG text            (before DATE/TIME set)
    """
    global log_head, log_count, log_overflow

    tag = _safe_text(tag)
    text = _safe_text(text)

    line = "[{}] {} {}".format(get_datetime_string(), tag, text)
    data = line.encode("utf-8", "ignore")

    if len(data) > LOG_LINE_MAX:
        if LOG_LINE_MAX >= 3:
            data = data[:LOG_LINE_MAX - 3] + b"..."
        else:
            data = data[:LOG_LINE_MAX]

    offset = log_head * LOG_LINE_MAX
    log_storage[offset:offset + len(data)] = data
    log_lengths[log_head] = len(data)

    log_head = (log_head + 1) % LOG_LINE_COUNT
    if log_count < LOG_LINE_COUNT:
        log_count += 1
    else:
        log_overflow = True

    print(line)

def log_boot():
    log_store("SYS", "BOOT START")
    log_store("SYS", "UART_CH={}".format(ACTIVE_UART_CH))
    log_store("SYS", "UART_BAUD={}".format(UART_BAUD))
    log_store("SYS", "I2C=I2C1 SDA=GP2 SCL=GP3 FREQ={}".format(I2C_FREQ))
    log_store("SYS", "PMBUS_ADDR=0x{:02X}".format(PMBUS_ADDR))
    log_store("SYS", "PEC={}".format("ON" if PEC_ENABLE else "OFF"))
    log_store("SYS", "RTC={}".format("VALID" if rtc_valid else "UNSET"))

# =========================================================
# RAM log read utility (NEW)
# =========================================================
def get_log_index_position(index_from_oldest):
    """
    Convert logical log index to ring buffer position.
    index_from_oldest:
      0 = oldest
      log_count - 1 = newest
    """
    if log_count == 0:
        raise ValueError("NO_LOG")

    if index_from_oldest < 0 or index_from_oldest >= log_count:
        raise ValueError("LOG_INDEX_RANGE")

    oldest_pos = (log_head - log_count) % LOG_LINE_COUNT
    pos = (oldest_pos + index_from_oldest) % LOG_LINE_COUNT
    return pos

def get_log_line(index_from_oldest):
    """
    Read one log line by logical index.
    0 = oldest, log_count-1 = newest
    """
    pos = get_log_index_position(index_from_oldest)
    offset = pos * LOG_LINE_MAX
    length = log_lengths[pos]
    data = log_storage[offset:offset + length]
    return data.decode("utf-8", "ignore")

# =========================================================
# Utility
# =========================================================
def uart_send_line(text):
    text = _safe_text(text)
    uart.write((text + "\r").encode("utf-8"))
    log_store("TX", text)

def to_signed(value, bits):
    if value & (1 << (bits - 1)):
        value -= (1 << bits)
    return value

def crc8_itu_xor55(data_bytes):
    """
    PEC:
      CRC-8/ITU
      Polynomial = x^8 + x^2 + x + 1 (0x07)
      Init       = 0x00
      XOROUT     = 0x55
    """
    crc = 0x00
    for b in data_bytes:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    crc ^= 0x55
    return crc & 0xFF

def decode_linear11(word):
    exponent_raw = (word >> 11) & 0x1F
    mantissa_raw = word & 0x07FF

    exponent = to_signed(exponent_raw, 5)
    mantissa = to_signed(mantissa_raw, 11)

    value = mantissa * (2 ** exponent)
    return value, exponent, mantissa

def status_to_bit_string(status_byte):
    return "{:08b}".format(status_byte)

def fw_to_string(raw):
    # PMBus受信1byte値を HEX 2桁文字列で返す
    # 例: 0x10 -> "10"
    return "{:02X}".format(raw & 0xFF)

# =========================================================
# Date / Time handlers
# =========================================================
def apply_datetime_if_ready():
    global rtc_valid, pending_date, pending_time

    if pending_date is None or pending_time is None:
        return False

    y, mo, d = pending_date
    hh, mm, ss = pending_time

    rtc.datetime((y, mo, d, 0, hh, mm, ss, 0))
    rtc_valid = True
    return True

def handle_date_set(date_str):
    global pending_date

    if len(date_str) != 8 or not date_str.isdigit():
        return "ERR:DATE_FORMAT"

    y = int(date_str[0:4])
    mo = int(date_str[4:6])
    d = int(date_str[6:8])

    if y < 2000:
        return "ERR:DATE_RANGE"
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return "ERR:DATE_RANGE"

    pending_date = (y, mo, d)
    applied = apply_datetime_if_ready()

    log_store("RTC", "DATE_SET={}".format(date_str))
    if applied:
        log_store("RTC", "DATETIME_VALID")

    return date_str

def handle_time_set(time_str):
    global pending_time

    if len(time_str) != 6 or not time_str.isdigit():
        return "ERR:TIME_FORMAT"

    hh = int(time_str[0:2])
    mm = int(time_str[2:4])
    ss = int(time_str[4:6])

    if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
        return "ERR:TIME_RANGE"

    pending_time = (hh, mm, ss)
    applied = apply_datetime_if_ready()

    log_store("RTC", "TIME_SET={}".format(time_str))
    if applied:
        log_store("RTC", "DATETIME_VALID")

    return time_str

def handle_date_read():
    if not rtc_valid:
        return "UNSET"

    dt = rtc.datetime()
    return "{:04d}{:02d}{:02d}".format(dt[0], dt[1], dt[2])

def handle_time_read():
    if not rtc_valid:
        return "UNSET"

    dt = rtc.datetime()
    return "{:02d}{:02d}{:02d}".format(dt[4], dt[5], dt[6])

def handle_datetime_read():
    if not rtc_valid:
        return "UNSET"

    dt = rtc.datetime()
    return "{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}".format(
        dt[0], dt[1], dt[2], dt[4], dt[5], dt[6]
    )

# =========================================================
# PMBus low-level
# =========================================================
def pmbus_write(command, data_bytes=None, pec_enable=True):
    if data_bytes is None:
        data_bytes = []

    payload = bytes([command] + list(data_bytes))

    if pec_enable:
        addr_w = (PMBUS_ADDR << 1) | 0
        pec = crc8_itu_xor55(bytes([addr_w]) + payload)
        payload += bytes([pec])

    i2c.writeto(PMBUS_ADDR, payload)

def pmbus_read(command, read_len, pec_enable=True):
    i2c.writeto(PMBUS_ADDR, bytes([command]), False)

    if pec_enable:
        resp = i2c.readfrom(PMBUS_ADDR, read_len + 1)
        data = resp[:-1]
        pec_rx = resp[-1]

        addr_w = (PMBUS_ADDR << 1) | 0
        addr_r = (PMBUS_ADDR << 1) | 1
        pec_calc = crc8_itu_xor55(bytes([addr_w, command, addr_r]) + data)

        if pec_rx != pec_calc:
            raise ValueError(
                "PEC mismatch cmd=0x{:02X} rx=0x{:02X} calc=0x{:02X}".format(
                    command, pec_rx, pec_calc
                )
            )
        return data
    else:
        return i2c.readfrom(PMBUS_ADDR, read_len)

# =========================================================
# PMBus high-level
# =========================================================
def set_page(page):
    pmbus_write(CMD_PAGE, [page], PEC_ENABLE)

def get_page():
    data = pmbus_read(CMD_PAGE, 1, PEC_ENABLE)
    return data[0]

def read_status():
    data = pmbus_read(CMD_STATUS_MFR, 1, PEC_ENABLE)
    return data[0]

def read_fw_ctrl():
    data = pmbus_read(CMD_FW_CTRL, 1, PEC_ENABLE)
    return data[0]

def read_fw_comm():
    data = pmbus_read(CMD_FW_COMM, 1, PEC_ENABLE)
    return data[0]

def read_vout(page):
    set_page(page)
    data = pmbus_read(CMD_READ_VOUT, 2, PEC_ENABLE)
    word = (data[1] << 8) | data[0]
    return word, decode_linear11(word)

def read_iout(page):
    set_page(page)
    data = pmbus_read(CMD_READ_IOUT, 2, PEC_ENABLE)
    word = (data[1] << 8) | data[0]
    return word, decode_linear11(word)

# =========================================================
# Retry wrapper
# =========================================================
def run_with_retry(func):
    last_exc = None
    for retry in range(RETRY_COUNT + 1):
        try:
            result = func()
            return result, retry
        except Exception as e:
            last_exc = e
    raise last_exc

# =========================================================
# Command handlers
# =========================================================
def handle_status():
    value, retry = run_with_retry(read_status)

    # ログは従来どおり詳細を残す
    log_store(
        "MEAS",
        "STATUS=Bit{},RETRY={}".format(status_to_bit_string(value), retry)
    )

    # ATE返信はデータのみ
    return status_to_bit_string(value)

def handle_status_bit(bit_no):
    value, retry = run_with_retry(read_status)
    bit_val = (value >> bit_no) & 0x01

    # ログは従来どおり詳細を残す
    log_store(
        "MEAS",
        "STATUS_{:02d}={},RETRY={}".format(bit_no, bit_val, retry)
    )

    # ATE返信はデータのみ
    return "{}".format(bit_val)

def handle_page_read():
    value, retry = run_with_retry(get_page)
    return "PAGE={:02X},RETRY={}".format(value, retry)

def handle_page_write(page):
    _, retry = run_with_retry(lambda: set_page(page))
    return "PAGE={:02X},RETRY={}".format(page, retry)

def handle_vout5():
    (raw, decoded), retry = run_with_retry(lambda: read_vout(PAGE_5V))
    value, exponent, mantissa = decoded

    log_store(
        "MEAS",
        "VOUT5={:.4f}V,RAW=0x{:04X},N={},Y={},RETRY={}".format(
            value, raw, exponent, mantissa, retry
        )
    )

    return "{:.4f}".format(value)

def handle_vout33():
    (raw, decoded), retry = run_with_retry(lambda: read_vout(PAGE_33V))
    value, exponent, mantissa = decoded

    log_store(
        "MEAS",
        "VOUT33={:.4f}V,RAW=0x{:04X},N={},Y={},RETRY={}".format(
            value, raw, exponent, mantissa, retry
        )
    )

    return "{:.4f}".format(value)

def handle_iout5():
    (raw, decoded), retry = run_with_retry(lambda: read_iout(PAGE_5V))
    value, exponent, mantissa = decoded

    log_store(
        "MEAS",
        "IOUT5={:.4f}A,RAW=0x{:04X},N={},Y={},RETRY={}".format(
            value, raw, exponent, mantissa, retry
        )
    )

    return "{:.4f}".format(value)

def handle_iout33():
    (raw, decoded), retry = run_with_retry(lambda: read_iout(PAGE_33V))
    value, exponent, mantissa = decoded

    log_store(
        "MEAS",
        "IOUT33={:.4f}A,RAW=0x{:04X},N={},Y={},RETRY={}".format(
            value, raw, exponent, mantissa, retry
        )
    )

    return "{:.4f}".format(value)

def handle_fw_ctrl():
    value, retry = run_with_retry(read_fw_ctrl)

    fw_text = fw_to_string(value)

    # ログは詳細を残す
    log_store(
        "MEAS",
        "FW_CTRL=0x{:02X},ATE={},RETRY={}".format(value, fw_text, retry)
    )

    # ATE返信はHEX 2桁文字列のみ
    return fw_text

def handle_fw_comm():
    value, retry = run_with_retry(read_fw_comm)

    fw_text = fw_to_string(value)

    # ログは詳細を残す
    log_store(
        "MEAS",
        "FW_COMM=0x{:02X},ATE={},RETRY={}".format(value, fw_text, retry)
    )

    # ATE返信はHEX 2桁文字列のみ
    return fw_text

def handle_error_all():
    status, r1 = run_with_retry(read_status)
    (v33_raw, v33_dec), r2 = run_with_retry(lambda: read_vout(PAGE_33V))
    (i33_raw, i33_dec), r3 = run_with_retry(lambda: read_iout(PAGE_33V))
    (v5_raw, v5_dec), r4 = run_with_retry(lambda: read_vout(PAGE_5V))
    (i5_raw, i5_dec), r5 = run_with_retry(lambda: read_iout(PAGE_5V))

    v33, _, _ = v33_dec
    i33, _, _ = i33_dec
    v5, _, _ = v5_dec
    i5, _, _ = i5_dec

    total_retry = r1 + r2 + r3 + r4 + r5

    log_store(
        "MEAS",
        "ERROR_ALL STATUS={},I5={:.4f}A,V5={:.4f}V,I33={:.4f}A,V33={:.4f}V,RETRY={}".format(
            status_to_bit_string(status),
            i5,
            v5,
            i33,
            v33,
            total_retry
        )
    )

    return (
        "STATUS={}"
        ",I5={:.4f}"
        ",V5={:.4f}"
        ",I33={:.4f}"
        ",V33={:.4f}"
        ",RETRY={}"
    ).format(
        status_to_bit_string(status),
        i5,
        v5,
        i33,
        v33,
        total_retry
    )

def handle_pec_on():
    global PEC_ENABLE
    PEC_ENABLE = True
    return "PEC=ON"

def handle_pec_off():
    global PEC_ENABLE
    PEC_ENABLE = False
    return "PEC=OFF"

def handle_pmb_rw(cmd_hex):
    cmd = int(cmd_hex, 16)
    data, retry = run_with_retry(lambda: pmbus_read(cmd, 2, PEC_ENABLE))
    word = (data[1] << 8) | data[0]
    value, exponent, mantissa = decode_linear11(word)
    return "PMB_RW_{}=0x{:04X},{:.4f},N={},Y={},RETRY={}".format(
        cmd_hex, word, value, exponent, mantissa, retry
    )

def handle_pmb_rb(cmd_hex):
    cmd = int(cmd_hex, 16)
    data, retry = run_with_retry(lambda: pmbus_read(cmd, 1, PEC_ENABLE))
    return "PMB_RB_{}=0x{:02X},RETRY={}".format(cmd_hex, data[0], retry)

def handle_any_write(cmd_hex, data_hex):
    cmd = int(cmd_hex, 16)
    dat = int(data_hex, 16)
    _, retry = run_with_retry(lambda: pmbus_write(cmd, [dat], PEC_ENABLE))
    return "ANY_WRITE CMD=0x{:02X},DATA=0x{:02X},RETRY={}".format(cmd, dat, retry)

# =========================================================
# Log handlers (NEW)
# =========================================================
def handle_log_info():
    return "LOG_COUNT={},LOG_MAX={},OVERFLOW={}".format(
        log_count,
        LOG_LINE_COUNT,
        1 if log_overflow else 0
    )

def handle_log_last():
    if log_count == 0:
        return "ERR:NO_LOG"

    return get_log_line(log_count - 1)

def handle_log_idx(index_text):
    try:
        index_no = int(index_text)
    except ValueError:
        return "ERR:LOG_INDEX_FORMAT"

    if log_count == 0:
        return "ERR:NO_LOG"

    if index_no < 0 or index_no >= log_count:
        return "ERR:LOG_INDEX_RANGE"

    return get_log_line(index_no)

def handle_log_clear():
    global log_storage, log_lengths, log_head, log_count, log_overflow

    log_storage = bytearray(LOG_LINE_MAX * LOG_LINE_COUNT)
    log_lengths = bytearray(LOG_LINE_COUNT)
    log_head = 0
    log_count = 0
    log_overflow = False

    # クリア操作自体は残す
    log_store("SYS", "LOG CLEARED")
    return "LOG=CLEARED"

# =========================================================
# Command parser
# =========================================================
def process_command(cmd):
    if cmd == "*IDN?":
        return "RP2040_PMBUS_BRIDGE,Ver1.00"

    elif cmd.startswith("DATE_"):
        return handle_date_set(cmd[5:])

    elif cmd.startswith("TIME_"):
        return handle_time_set(cmd[5:])

    elif cmd == "DATE?":
        return handle_date_read()

    elif cmd == "TIME?":
        return handle_time_read()

    elif cmd == "DATETIME?":
        return handle_datetime_read()

    elif cmd == "STATUS?":
        return handle_status()

    elif cmd.startswith("STATUS_") and cmd.endswith("?"):
        try:
            bit_no = int(cmd[7:9])
        except ValueError:
            return "ERR:BIT_FORMAT"

        if 0 <= bit_no <= 7:
            return handle_status_bit(bit_no)
        return "ERR:BIT_RANGE"

    elif cmd == "PAGE?":
        return handle_page_read()

    elif cmd == "PAGE_02":
        return handle_page_write(PAGE_33V)

    elif cmd == "PAGE_03":
        return handle_page_write(PAGE_5V)

    elif cmd == "VOUT5?":
        return handle_vout5()

    elif cmd == "VOUT33?":
        return handle_vout33()

    elif cmd == "IOUT5?":
        return handle_iout5()

    elif cmd == "IOUT33?":
        return handle_iout33()

    elif cmd == "FW_CTRL?":
        return handle_fw_ctrl()

    elif cmd == "FW_COMM?":
        return handle_fw_comm()

    elif cmd == "ERROR_ALL?":
        return handle_error_all()

    elif cmd == "PEC_ON":
        return handle_pec_on()

    elif cmd == "PEC_OFF":
        return handle_pec_off()

    elif cmd == "LOG_INFO?":
        return handle_log_info()

    elif cmd == "LOG_LAST?":
        return handle_log_last()

    elif cmd.startswith("LOG_IDX_") and cmd.endswith("?"):
        return handle_log_idx(cmd[8:-1])

    elif cmd == "LOG_CLEAR":
        return handle_log_clear()

    elif cmd.startswith("PMB_RW_") and cmd.endswith("?"):
        return handle_pmb_rw(cmd[7:-1])

    elif cmd.startswith("PMB_RB_") and cmd.endswith("?"):
        return handle_pmb_rb(cmd[7:-1])

    elif cmd.startswith("ANY_WRITE_"):
        parts = cmd.split("_")
        if len(parts) == 4:
            return handle_any_write(parts[2], parts[3])
        return "ERR:FORMAT"

    return "ERR:Unknown Command"

# =========================================================
# UART receive loop
# =========================================================
def uart_send_receive():
    global rx_buffer

    while uart.any():
        ch = uart.read(1)
        if not ch:
            return

        if ch == b'\r' or ch == b'\n':
            if rx_buffer:
                cmd = rx_buffer.strip()
                log_store("RX", cmd)

                try:
                    response = process_command(cmd)
                except Exception as e:
                    response = "ERR:" + repr(e)

                uart_send_line(response)
                rx_buffer = ""
        else:
            try:
                rx_buffer += ch.decode("utf-8")
            except Exception:
                pass

# =========================================================
# Main loop
# =========================================================
log_boot()

while True:
    uart_send_receive()

    now = time.ticks_ms()
    if time.ticks_diff(now, last_blink) >= 500:
        led.value(0 if led.value() else 1)
        last_blink = now

    time.sleep_ms(10)