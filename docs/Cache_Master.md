# Cache / Invalidation / Post-Action Confirmation Master

通信仕様基準: `reference/RW11用電源通信仕様書r1.pdf`（GVT-284454-001-00、初版 2026/9/4）。基準切替日: 2026-09-07。D6は過去比較用。未確定事項・暫定値は引き続きOpen Issuesに従う。
Revision: Rev.0

## Cache list
DATA, STATUS, INFO, BC, AR, D2, D3, D4, EL_01, EL_09, EL_17, EL_25, OL_01, OL_09, OL_17, OL_25, OL_33, OL_41, OL_49, OL_57, FD.

Power-on: all INVALID.

## Rules
- Query never triggers NF55G communication.
- Refresh invalidates target before transaction.
- Refresh success -> VALID.
- Refresh failure -> remains INVALID.
- Never restore old cache after failed refresh.
- VALID means last fetch/decode was successful, not that the data is current now.
- Control response status does not update STATUS cache.

## Master
| Command | Success VALID | Success INVALID | Post |
|---|---|---|---|
| DATA_REFRESH | DATA | - | DATA query |
| STATUS_REFRESH | STATUS | - | STATUS query |
| INFO_REFRESH | INFO | - | INFO query |
| SP | - | DATA/STATUS/INFO | INFO_REFRESH |
| RP | - | DATA/STATUS/INFO | INFO_REFRESH |
| SE | - | DATA/STATUS | STATUS_REFRESH |
| SC | - | DATA/STATUS | DATA_REFRESH |
| SS | - | DATA/INFO | INFO_REFRESH |
| SL | - | DATA | DATA_REFRESH |
| BC START | BC | DATA/STATUS | BC query |
| BC STOP | - | BC/DATA/STATUS | STATUS_REFRESH |
| CN | - | DATA/STATUS | STATUS_REFRESH + ext current |
| CF | - | DATA/STATUS | STATUS_REFRESH + ext current |
| BE | - | DATA/STATUS | STATUS_REFRESH + ext 12V |
| BF | - | DATA/STATUS | STATUS_REFRESH + ext 12V |
| OR | - | DATA/STATUS | STATUS_REFRESH + ext 12V |
| D2 | D2 | DATA | optional DATA_REFRESH |
| D3 | D3 | DATA | optional DATA_REFRESH |
| D4 | D4 | DATA | optional DATA_REFRESH |
| EL | target block | - | EL query |
| OL | target block | - | OL query |
| CD | - | DATA/STATUS/BC | DATA+STATUS_REFRESH |
| CL | - | all EL/OL | EL/OL refresh |
| AD | - | DATA/AR | AR_REFRESH |
| AR | AR | - | AR query |
| FD | FD | old FD | none |
| FU | - | - | ERR:FU_DISABLED |

## Error policy
- Parser rejection: cache unchanged.
- PME/SQE/CME/MCM: existing cache generally unchanged; refresh target remains INVALID if refresh already started.
- ACK_TIMEOUT/RESP_TIMEOUT/final BCC/FRAME/UART/COMM: apply ambiguous invalidation same as success-invalidates.
- HWE: DATA/STATUS invalid at minimum.
