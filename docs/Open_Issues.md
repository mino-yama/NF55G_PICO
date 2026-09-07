# Open Issues
Revision: Rev.0
Codex must NOT close these by inference.

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
過去のAD/ARレビューにあるD6参照は当時の比較記録として保持する。r1への基準切替は既存Issueの解決・Closeを意味しない。

| ID | Issue | Rev.0 implementation |
|---|---|---|
| OI-01 | Pico-side T1 final value | 200 ms provisional |
| OI-02 | D0 T2 list=300ms vs detail=600ms | use 600 ms provisional |
| OI-03 | Current FW may clear CHARGE_END after D0 ACK | retain existing non-destructive D0 policy; confirm r1/final FW interpretation |
| OI-04 | AR REF/value8 final wire format and ATE return policy | Fixture draft keeps REF as raw8/open; interim FW appears to use IEEE754 float raw HEX. Decide raw/decode/both before final ATE release. |
| OI-05 | AD runtime coefficient immediate reflection vs reboot | Interim FW writes EEPROM and computes response-local slope, but runtime coefficient globals may not update immediately. No automatic reboot; confirm final behavior. |
| OI-06 | BC=0 STOP current FW behavior | implement spec; confirm final FW |
| OI-07 | BC MODE=13 response details | expose received data; confirm |
| OI-08 | SL out-of-range PME behavior | spec/FW confirmation |
| OI-09 | OR request while restart already active | current FW SQE; confirm |
| OI-10 | FD out-of-range address | current FW FF fill; confirm formal behavior |
| OI-11 | EB timing while command transaction active | keep original deadline; HIL confirm |
| OI-12 | AR T2 final value | confirm before final release |
| OI-13 | RTC HAT revision pin mapping | verify I2C scan 0x68 on received hardware |
| OI-14 | UNIT_ID source for future filename extension | product FW read vs barcode undecided |
| OI-15 | Detailed USB CDC/PySide6 protocol | deferred phase |
| OI-16 | AD request/response wire format mismatch | Fixture draft defines AD as 10-char DATA control/set command; interim FW request is `TYPE1+POINT1+VALUE8` and success response is `TYPE1+POINT1+ADC6+CALC8`. Confirm r1/production FW/design expectation. |
| OI-17 | AD/AR target mapping and 12VOUT_I coverage | Fixture draft/decoder expose five AR systems; interim FW implements the same five targets, while `12VOUT_I` has a runtime coefficient but no AD/AR EEPROM slot. Confirm final target list and ATE names. |
| OI-18 | AD POINT/VALUE validation and rejection policy mismatch | Fixture docs leave POINT/VALUE validation open; interim FW uses POINT `1/2`, clamps out-of-range VALUE, and may not explicitly reject unsupported TYPE/POINT. Define final PME/SQE/clamp behavior. |
| OI-19 | AD persistence/write timing and EEPROM error behavior | Interim FW stores `correct_t` to EEPROM and returns after write check; final commit timing, busy behavior, retention, write-cycle limits, and HWE behavior need confirmation. |
| OI-20 | AR response length/order final confirmation | Fixture draft and interim FW both indicate 140 DATA chars: five targets x two points x `(ADC6 + REF/value8)`. Verify final production FW order/length before fixing ATE query behavior. |
| OI-21 | AD calibration preconditions and HIL acceptance criteria | Fixture docs assign PASS/FAIL to ATE and external measurement; interim FW has no visible AD-specific state checks. Define allowed state/load/output/charger interlocks and measurement correlation criteria. |
| OI-22 | r1 BOOT update interruption recovery wording and procedure | r1 p.37 section 12.5.2 removes D6 automatic recovery within 1 second and requires BOOT retry writing, but the introduction still describes differing automatic-recovery availability and (1) duplicates USER wording in (2). Design must confirm the supported recovery sequence and applicable FW. FU remains prohibited in the Pico fixture; this does not block ordinary communication development. See `RW11_D6_to_R1_Impact_Review_20260907.md`. |
| HW-01 | ADA-5703 GP4/GP5 and Pico-2CH-RS232 UART1 pin conflict | Adafruit ADA-5703 PiCowbell PCF8523 RTC/I2C circuitry is physically connected to GP4=SDA and GP5=SCL, while Waveshare Pico-2CH-RS232 fixes NF55G UART1 to GP4=TX and GP5=RX. 2026-09-04 real-hardware SD/RTC tests were performed with ADA-5703 GP4/GP5 physically isolated. Keep open until the final fixture physical cut/isolation method and inspection record are formally documented. |

## AD/AR consolidated review notes

Reviewed documents:
- `AGENTS.md`
- `README.md`
- `docs/ATE_Command_Master.md`
- `docs/ATE_Command_List_for_Test_Program.md`
- `docs/Data_Decode_Master.md`
- `docs/Cache_Master.md`
- `docs/Protocol_State_Machine.md`
- `docs/Software_Module_Interface.md`
- `docs/Test_Specification.md`
- `docs/Implementation_Plan.md`
- `docs/Program_State_Transition_Diagram.md`
- `docs/Real_Hardware_Test_Log.md`
- `docs/CHANGELOG.md`
- `reference/RW11用電源通信仕様書d6.pdf`
- `reference/NF55G_試験治具仕様書_Rev0_正本.docx`
- `reference/NF55G_試験治具仕様書_添付資料_CN24通信ハーネス結線表.docx`
- `reference/NF54191-G_S1.docx`
- `reference/開発手順(ChatGPT→Codex引き渡し).docx`

Interim FW source checked:
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_define.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_tbl.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_serial.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_global.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_global.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_input.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_init.c`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_eeprom.h`
- `C:\Users\m_yamada\Desktop\NF55G\src\NF55_eeprom.c`

Consolidation map:
- OI-16 merges former OI-16, OI-20, and OI-29. The issue is one wire-format mismatch: fixture draft command/response expectation vs interim FW implementation.
- OI-17 merges former OI-17, OI-24, and OI-32. The issue is one target-list/mapping question: five AR systems vs runtime-only `12VOUT_I`.
- OI-18 merges former OI-18, OI-19, OI-27, and OI-28. The issue is one validation-policy question: accepted POINT/VALUE range and error/clamp behavior.
- OI-19 keeps former OI-21. Persistence/write behavior is separate from protocol field layout.
- OI-20 keeps the AR order/length part of former OI-24. REF representation and ATE return policy are tracked in OI-04 to avoid duplication.
- OI-21 merges former OI-22 and OI-26. Calibration preconditions and HIL acceptance belong together because both must be confirmed with production FW and design.
- OI-05 absorbs former OI-23 and OI-31. The issue is one reflection-timing question: EEPROM update vs runtime coefficient update vs reboot.

Detailed AD/AR differences:
- AD request/response format: `ATE_Command_Master.md` and `ATE_Command_List_for_Test_Program.md` define ATE command `AD_<TYPE>_<POINT>_<VALUE>` mapped to NF CMD `AD` with 10-char DATA, while interim FW parses DATA as `TYPE1 + POINT1 + VALUE8`. Current fixture docs treat AD as a control/set command, but interim FW returns success DATA `TYPE1 + POINT1 + ADC6 + CALC8`. Final production FW/D6-design expectation is not yet confirmed.
- AD VALUE/AR REF numeric representation: fixture docs intentionally keep AR `REF8` raw/open and do not finalize AD VALUE encoding. Interim FW uses `aschex_to_float()` and `float_to_aschex()`, which indicates IEEE754 float bit pattern encoded as 8 ASCII HEX chars. Endianness, ATE decoded display, and raw preservation policy must be decided.
- AD target mapping: fixture decoder and interim FW both indicate five calibration targets: `DISCHG_I`, `BATT_V`, `ACDC12V_V`, `BATT_CHG`, and `12VOUT_V`. Interim FW comments are narrower, describing battery voltage adjustment, and `12VOUT_I` has a runtime coefficient but no AD/AR EEPROM record. Final design must confirm whether `12VOUT_I` is intentionally non-adjustable.
- AD POINT/range handling: fixture docs leave POINT and VALUE validation as open design items. Interim FW maps POINT `1` to `point1/ad1` and POINT `2` to `point2/ad2`; unsupported TYPE/POINT may fall through without explicit PME/SQE, and out-of-range VALUE is clamped rather than rejected. Production FW must define whether invalid input is rejected, clamped, or treated as sequence/parameter error.
- AD persistence and reflection timing: interim FW writes calibration records to EEPROM and checks write completion, but successful AD appears to calculate response-local values without visibly updating runtime measurement coefficient globals such as `gf_batt_v_coeff`. This differs from an ATE expectation that immediate `AR_REFRESH` or subsequent measurements reflect AD. Confirm whether reboot, re-init, delay, or explicit refresh path is required.
- AR response shape: `Data_Decode_Master.md` defines AR as 140 DATA chars: five systems x two points x `(ADC6 + REF8)`. Interim FW matches 140 DATA chars and full frame length 146, ordered `DISCHG_I`, `BATT_V`, `ACDC12V_V`, `BATT_CHG`, `12VOUT_V`. This agreement still needs final production FW confirmation before the ATE query behavior is fixed.

Implementation cautions for AD/AR:
- Do not translate between tentative FW behavior and r1/design intent inside Pico. If interim FW behavior differs, expose it as an Open Issue and confirm with production FW/design.
- Keep AD implementation provisional until OI-16 through OI-21 and OI-04/OI-05 are answered. Parser strictness should follow the confirmed final format, not Codex inference.
- AD success or ambiguous failure must invalidate `DATA` and `AR`. ATE individual Query must not auto-refresh; ATE must explicitly run `AR_REFRESH` after AD.
- Do not update `AR` cache from AD response data unless final FW explicitly defines AD response as AR-equivalent.
- Do not update `STATUS` or `INFO` cache from AD/AR side effects, response status, D0 embedded status, or EB events.
- Treat AD `OK` as protocol success only. Calibration correctness, product behavior, and measurement PASS/FAIL remain ATE/design responsibility.
- For HIL, log raw AD frame DATA, AD result, retry counts, ambiguous flag, elapsed time, AR raw response, decoded ADC values, REF raw values, and external measurement values.
- Before final release, test each AR system, P1/P2, nominal/min/max/out-of-range AD values, malformed AD fields, power-cycle retention, immediate AR after AD, delayed AR after AD, and reboot-required behavior if applicable.
