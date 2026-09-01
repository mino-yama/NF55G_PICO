"""Project-wide constants for the NF55G Pico fixture."""

STX = 0x02
ETX = 0x03
ACK = 0x06
NAK = 0x15

NF55_BAUDRATE = 38400
NF55_BITS = 8
NF55_PARITY = "even"
NF55_STOP_BITS = 1

T1_ACK_TIMEOUT_MS = 200
T2_DEFAULT_MS = 100
T2_D0_MS = 600
T2_BC_MS = 6000

MAX_COMMAND_RETRY = 1
MAX_RESPONSE_RETRY = 1

NAK_RETRY_REASONS = ("30", "31", "32", "33", "35", "36")
NF55_ERROR_CODES = ("CME", "PME", "SQE", "HWE", "MCM", "FUE")

AMBIGUOUS_ERRORS = (
    "ACK_TIMEOUT",
    "RESP_TIMEOUT",
    "FINAL_BCC_FRAME",
    "UART",
    "COMM",
    "HWE",
)

CACHE_NAMES = (
    "DATA",
    "STATUS",
    "INFO",
    "BC",
    "AR",
    "D2",
    "D3",
    "D4",
    "EL_01",
    "EL_09",
    "EL_17",
    "EL_25",
    "OL_01",
    "OL_09",
    "OL_17",
    "OL_25",
    "OL_33",
    "OL_41",
    "OL_49",
    "OL_57",
    "FD",
)

EL_CACHE_NAMES = ("EL_01", "EL_09", "EL_17", "EL_25")
OL_CACHE_NAMES = (
    "OL_01",
    "OL_09",
    "OL_17",
    "OL_25",
    "OL_33",
    "OL_41",
    "OL_49",
    "OL_57",
)

REFRESH_TARGETS = {
    "DATA_REFRESH": "DATA",
    "STATUS_REFRESH": "STATUS",
    "INFO_REFRESH": "INFO",
    "D2_REFRESH": "D2",
    "D3_REFRESH": "D3",
    "D4_MAINT_READ": "D4",
    "AR_REFRESH": "AR",
}

SUCCESS_INVALIDATION = {
    "SP": ("DATA", "STATUS", "INFO"),
    "RP": ("DATA", "STATUS", "INFO"),
    "SE": ("DATA", "STATUS"),
    "SC": ("DATA", "STATUS"),
    "SS": ("DATA", "INFO"),
    "SL": ("DATA",),
    "BC_START": ("DATA", "STATUS"),
    "BC_STOP": ("BC", "DATA", "STATUS"),
    "CN": ("DATA", "STATUS"),
    "CF": ("DATA", "STATUS"),
    "BE": ("DATA", "STATUS"),
    "BF": ("DATA", "STATUS"),
    "OR": ("DATA", "STATUS"),
    "D2": ("DATA",),
    "D3": ("DATA",),
    "D4": ("DATA",),
    "CD": ("DATA", "STATUS", "BC"),
    "CL": EL_CACHE_NAMES + OL_CACHE_NAMES,
    "AD": ("DATA", "AR"),
}
