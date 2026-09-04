# Hardware Reference Alignment Check
Revision: Rev.0-draft
Date: 2026-09-04

## Scope
Checked the saved local reference package against the current NF55G Pico 2 fixture development baseline.

Reference package:
- `docs/NF55G_RTC_SD_RS232C2ch_local_reference_package_20260904.zip`

Organized local reference folder:
- `reference/local_hardware_reference_20260904/`

Main checked files after temporary extraction:
- `NF55G_local_reference_package/README.md`
- `NF55G_local_reference_package/00_README_and_index/MATERIALS_INDEX.md`
- `NF55G_local_reference_package/00_README_and_index/NF55G_ALIGNMENT_CHECK.md`, after removing other-product serial-communication references from the organized local copy
- Waveshare Pico-RTC-DS3231 official sample code and saved pages
- Adafruit ADA-5703 PiCowbell Adalogger saved guide and PCB files
- Waveshare Pico-2CH-RS232 official sample code and saved pages
- Current project `README.md`, `docs/Logger_SD_Spec.md`, `docs/Software_Module_Interface.md`, `docs/Test_Specification.md`, `docs/Open_Issues.md`, and `docs/Real_Hardware_Test_Log.md`

## Current NF55G Pico fixture baseline
| Function | Current fixture assignment | Status |
|---|---|---|
| ATE RS-232C / UART0 | GP0=TX, GP1=RX | Keep |
| NF55G RS-232C / UART1 | GP4=TX, GP5=RX, 38400 bps, 8E1 | Keep |
| DS3231 RTC | I2C0, GP20=SDA, GP21=SCL, address `0x68` | Keep |
| ADA-5703 microSD | SPI0, GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI | Keep |
| ADA-5703 PCF8523 / STEMMA QT I2C | GP4=SDA, GP5=SCL | Not used; physically isolated for 2026-09-04 tests |

## Alignment result
| Area | Reference finding | Current project | Assessment |
|---|---|---|---|
| RS-232C 2CH | Waveshare sample/wiki use CH0 UART0 GP0/GP1 and CH1 UART1 GP4/GP5 | `README.md` and `Implementation_Plan.md` use ATE GP0/GP1 and NF55G GP4/GP5 | Aligned |
| NF55G UART settings | Project requires NF55G 38400 bps, 8E1 from D6/project specs | Current project uses 38400 bps, 8E1 | Aligned; Waveshare sample baudrate is only a board demo |
| DS3231 address | DS3231 sample uses address `0x68` | `DS3231I2CDevice` uses `0x68` | Aligned |
| DS3231 pins | Waveshare Python sample uses SDA=GP20, SCL=GP21 | Current project uses SDA=GP20, SCL=GP21 | Aligned and verified on hardware |
| SD pins | Adafruit ADA-5703 uses GP16=MISO, GP17=CS, GP18=SCK, GP19=MOSI | Current project uses the same SD-only pin set | Aligned and verified on hardware |
| Card detect | ADA-5703 optional card-detect jumper can use GP15 | Current project does not require card detect | No drift; optional feature remains unused |
| ADA-5703 I2C | ADA-5703 PCF8523/STEMMA QT uses GP4/GP5 and RTC address `0x68` | Current project reserves GP4/GP5 for NF55G UART1 and uses DS3231 as RTC | Aligned only when GP4/GP5 are physically isolated and PCF8523 is not used |

## Important notes
- Other-product serial communication examples are kept only as reference material. Do not use their pin assignments or product behavior as the current NF55G Pico fixture baseline.
- In the current NF55G Pico fixture, GP16-GP19 are intentionally allocated to ADA-5703 microSD, and GP20/GP21 are intentionally allocated to DS3231.
- A Waveshare C sample header appears to name `I2C_SCL=20` and `I2C_SDA=21`, while the Waveshare Python sample and the actual 2026-09-04 hardware verification confirm DS3231 operation with SDA=GP20 and SCL=GP21. Do not change the current implementation based only on that C sample naming.
- ADA-5703 GP4/GP5 were physically isolated for the 2026-09-04 real-hardware SD/RTC tests. HW-01 should remain open until the final fixture cut/isolation method and inspection record are documented.

## Conclusion
No immediate development drift was found between the saved RTC/SD/RS232 reference package and the current NF55G Pico fixture baseline.

The current design direction remains valid:
1. Use Waveshare Pico-2CH-RS232 CH0 for ATE on GP0/GP1.
2. Use Waveshare Pico-2CH-RS232 CH1 for NF55G on GP4/GP5.
3. Use Waveshare Pico-RTC-DS3231 on I2C0 GP20/GP21 as the fixture RTC.
4. Use ADA-5703 only for microSD on GP16-GP19.
5. Keep ADA-5703 PCF8523/STEMMA QT GP4/GP5 isolated and unused in this fixture.

## Follow-up
- The original `docs/NF55G_RTC_SD_RS232C2ch_local_reference_package_20260904.zip` was extracted, reorganized, and deleted.
- Use `reference/local_hardware_reference_20260904/required_for_development/` for current fixture implementation references.
- Use `reference/local_hardware_reference_20260904/reference_only/` for general/historical/original-distribution material.
- If final fixture hardware differs from the 2026-09-04 physically isolated setup, re-run this alignment check before UART loopback and real NF55G HIL.
