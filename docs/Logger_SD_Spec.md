# Logger / SD Card Specification

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0

## Hardware
- Adafruit ADA-5703 PiCowbell Data Logger
- microSD 32GB
- FAT32
- Known hardware issue: ADA-5703 PCF8523 RTC/I2C circuitry is physically connected to GP4/GP5, which conflicts with Pico-2CH-RS232 NF55G UART1 on GP4/GP5. See `docs/Open_Issues.md` HW-01 before using this board in the final fixture.
- Intended SD-only pin use remains GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI after the GP4/GP5 conflict is resolved by hardware action.

## Format
- CSV
- filename: `YYYYMMDD_HHMMSS.csv`
- RTC source: Pico-side DS3231

## Production
ATE sends:
- TEST_START
- TEST_END

One production test = one CSV file.
TEST_END performs forced queue drain, flush and close.

## Evaluation
- LOG_CONT_START
- LOG_CONT_STOP
Long-running file rollover size is configurable; 100MB recommended initial value.

## Flush
Normal flush condition:
- 1 second elapsed, OR
- 32 records accumulated,
whichever occurs first.

Hard rule:
No SD file write/flush during critical NF55G protocol states.
Protocol timing has priority; log records go to RAM queue.

## Capacity / rotation
Use 90% of SD capacity.
- BANK_A 45%
- BANK_B 45%
- Reserve 10%

Ping-pong:
A fills -> B
B fills -> erase/reuse old A
repeat

Implement as directories/logical banks on one FAT32 volume, not separate partitions.

## SD failure
SD failure must NOT stop product test or NF55G communication.
Latched states:
- OK
- NO_CARD
- MOUNT_ERR
- OPEN_ERR
- WRITE_ERR
- FULL

ATE maintenance commands:
- SD_STATUS?
- SD_USAGE?
- LOG_DROP_COUNT?
- SD_REINIT

## Multi-sink logger
Logger architecture supports:
- SD sink
- future USB sink
- REPL/debug sink

USB logging must be non-blocking and may drop logs rather than delay ATE/NF55G.

Priority:
1. ATE
2. complete current NF55G transaction safely
3. mandatory internal processing
4. SD logger
5. future USB logger

## Suggested CSV fields
timestamp,category,direction,cmd,event,raw_ascii,raw_hex,bcc_rx,bcc_calc,bcc_ok,cmd_retry,rsp_retry,result,detail
