# NF55G Pico 2 Hardware Local References
Revision: Rev.0-draft
Date: 2026-09-04

This folder is the extracted and reorganized replacement for:

- `docs/NF55G_RTC_SD_RS232C2ch_local_reference_package_20260904.zip`

The original ZIP was deleted after extraction and classification.

## Folder Policy
| Folder | Purpose |
|---|---|
| `required_for_development/` | Materials needed when implementing or checking the current NF55G Pico 2 fixture hardware layers. |
| `reference_only/` | General Pico documents, other project RS-232 examples, duplicate original archives, UF2 demo images, and other materials not used as the current fixture baseline. |

## Required For Development
| Folder | Contents | Why it is required |
|---|---|---|
| `00_index_and_alignment/` | Material index, package checksum list, original alignment note | Provenance and quick traceability. |
| `01_rtc_waveshare_pico_rtc_ds3231/` | DS3231 official pages, schematic, datasheet, Python/C samples | Current fixture RTC is DS3231 on I2C0 GP20/GP21, address `0x68`. |
| `02_sd_adafruit_ada5703_picowbell/` | ADA-5703 guide, product page, PCF8523 datasheet, PCB files, sample | Current fixture uses ADA-5703 microSD on GP16-GP19 and must keep PCF8523/STEMMA GP4/GP5 isolated. |
| `03_rs232c_waveshare_pico_2ch_rs232/` | Pico-2CH-RS232 official pages, schematic, SP3232EEN datasheet, Python/C samples | Current fixture uses CH0 GP0/GP1 for ATE and CH1 GP4/GP5 for NF55G. |
| `04_nf55g_connector/` | CN24 harness reference document | Needed for final NF55G wiring/HIL checks. |

## Reference Only
| Folder | Contents | Note |
|---|---|---|
| `common_pico_docs/` | Raspberry Pi/Waveshare general Pico getting-started PDFs | Useful setup background, not fixture-specific. |
| `micropython_official_docs/` | Saved MicroPython Pin/I2C/SPI/UART/RP2 API pages | API reference. Current code remains the source of fixture behavior. |
| `other_project_rs232_examples/` | Other project RS-232 examples | Reference only; do not treat pin assignments here as the current NF55G Pico fixture baseline. |
| `original_download_archives_and_uf2/` | Original downloaded ZIP/7z archives and UF2 demo images | Preserved for provenance/recovery, not for direct fixture flashing without review. |

## Current Fixture Baseline
| Function | Current assignment |
|---|---|
| ATE RS-232C / UART0 | GP0=TX, GP1=RX |
| NF55G RS-232C / UART1 | GP4=TX, GP5=RX, 38400 bps, 8E1 |
| DS3231 RTC | I2C0, GP20=SDA, GP21=SCL, address `0x68` |
| ADA-5703 microSD | SPI0, GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI |
| ADA-5703 PCF8523/STEMMA QT | Not used; GP4/GP5 physically isolated for 2026-09-04 tests |

## Cautions
- `reference_only/other_project_rs232_examples/` contains serial communication examples from other products. Use them only for UART handling style, not for NF55G Pico fixture pin assignments or behavior.
- Waveshare DS3231 C sample naming has an SCL/SDA ambiguity. The current fixture follows the Waveshare Python sample and the verified hardware result: SDA=GP20 and SCL=GP21.
- Do not use demo UF2 files in `reference_only/original_download_archives_and_uf2/` as fixture firmware without review.
- HW-01 remains open until the final fixture GP4/GP5 isolation method and inspection record are documented.

## Related Project Note
See also:

- `docs/Hardware_Reference_Alignment_Check_20260904.md`
