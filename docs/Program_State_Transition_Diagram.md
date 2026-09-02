# Program State Transition Diagram
Revision: Rev.0-draft
Date: 2026-09-02

## 1. 目的
本書は、NF55G Pico 試験治具ソフトウェアのプログラム遷移、および NF55G protocol transaction の遷移図を準備するための文書である。

実装・試験・レビュー時に、処理の責務分離と state transition を確認するために使用する。

## 2. 適用範囲
- 全体プログラムの起動/待受/コマンド処理/保守処理の概要遷移。
- NF55G 1 transaction の ACK/NAK/timeout/response retry 遷移。
- EB event の扱い。

対象外:
- 製品 PASS/FAIL 判定。これは ATE 側責務。
- USB CDC 詳細 protocol。Rev.0 では deferred。
- Real NF55G HIL で未確定の timing 差異の確定。

## 3. 全体プログラム遷移

```mermaid
stateDiagram-v2
    [*] --> BOOT
    BOOT --> INIT_HW: power on
    INIT_HW --> INIT_CACHE: UART/I2C/RTC/Logger init
    INIT_CACHE --> IDLE: cache INVALID

    IDLE --> ATE_COMMAND_RECEIVED: ATE command line
    IDLE --> USB_MAINT_RECEIVED: future USB maintenance command
    IDLE --> EB_EVENT_RECEIVED: NF55G EB event
    IDLE --> LOGGER_SERVICE: logger service tick

    ATE_COMMAND_RECEIVED --> PARSE_COMMAND
    USB_MAINT_RECEIVED --> PARSE_COMMAND: same command core

    PARSE_COMMAND --> QUERY_CACHE: cache query
    PARSE_COMMAND --> REFRESH_TRANSACTION: refresh/read
    PARSE_COMMAND --> CONTROL_TRANSACTION: control/set/clear
    PARSE_COMMAND --> RTC_COMMAND: RTC command
    PARSE_COMMAND --> LOGGER_COMMAND: logger command
    PARSE_COMMAND --> DIAGNOSTIC_COMMAND: diagnostic command
    PARSE_COMMAND --> PARSER_ERROR: syntax/parameter error

    QUERY_CACHE --> RETURN_RESPONSE: cache VALID
    QUERY_CACHE --> RETURN_ERROR: cache INVALID

    REFRESH_TRANSACTION --> NF55_TRANSACTION
    CONTROL_TRANSACTION --> NF55_TRANSACTION
    DIAGNOSTIC_COMMAND --> NF55_TRANSACTION: NF_COMM_CHECK only

    NF55_TRANSACTION --> CACHE_UPDATE: success refresh
    NF55_TRANSACTION --> CACHE_INVALIDATE: control success or ambiguous failure
    NF55_TRANSACTION --> RETURN_ERROR: failure

    CACHE_UPDATE --> RETURN_RESPONSE
    CACHE_INVALIDATE --> RETURN_RESPONSE
    RTC_COMMAND --> RETURN_RESPONSE
    LOGGER_COMMAND --> RETURN_RESPONSE
    PARSER_ERROR --> RETURN_ERROR

    EB_EVENT_RECEIVED --> EB_DECODE_ACK
    EB_DECODE_ACK --> IDLE: do not update STATUS cache

    LOGGER_SERVICE --> IDLE: no write/flush during protocol busy
    RETURN_RESPONSE --> IDLE
    RETURN_ERROR --> IDLE
```

## 4. NF55G Transaction 詳細遷移

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> PREPARE: transact(cmd,data)
    PREPARE --> TX_COMMAND: frame ready
    TX_COMMAND --> WAIT_ACK: command sent

    WAIT_ACK --> WAIT_RESPONSE: ACK
    WAIT_ACK --> COMMAND_RETRY: NAK30/31/32/33/35/36 and retry available
    WAIT_ACK --> COMMAND_RETRY: ACK_TIMEOUT and retry available
    WAIT_ACK --> FAILED: final NAK or final ACK_TIMEOUT

    COMMAND_RETRY --> TX_COMMAND: resend same command

    WAIT_RESPONSE --> RECEIVE_RESPONSE: frame received
    WAIT_RESPONSE --> COMMAND_RETRY: RESP_TIMEOUT and retry available
    WAIT_RESPONSE --> FAILED: final RESP_TIMEOUT

    RECEIVE_RESPONSE --> VALIDATE_RESPONSE: frame complete

    VALIDATE_RESPONSE --> TX_RESPONSE_ACK: valid normal response
    VALIDATE_RESPONSE --> TX_RESPONSE_ACK: valid error response
    VALIDATE_RESPONSE --> TX_RESPONSE_NAK: BCC/frame/CMD/length NG

    TX_RESPONSE_NAK --> WAIT_RESPONSE_RETRY: plain NAK 0x15 sent
    WAIT_RESPONSE_RETRY --> VALIDATE_RESPONSE: response retransmission received
    WAIT_RESPONSE_RETRY --> FAILED: final response retry failure

    TX_RESPONSE_ACK --> SUCCESS: normal response ACK sent
    TX_RESPONSE_ACK --> FAILED: error response ACK sent

    SUCCESS --> IDLE: result returned
    FAILED --> IDLE: result returned
```

## 5. Cache 影響の概要

```mermaid
flowchart TD
    A[ATE Command] --> B{Command type}
    B -->|Individual Query| C{Cache VALID?}
    C -->|Yes| D[Return cached value]
    C -->|No| E[ERR:CACHE_INVALID]

    B -->|Refresh / Read| F[Invalidate target cache first]
    F --> G[NF55G Transaction]
    G -->|Success + full decode| H[Validate target cache]
    G -->|Failure / partial decode| I[Keep target INVALID]

    B -->|Control / Set / Clear| J[NF55G Transaction]
    J -->|Success| K[Invalidate specified related caches]
    J -->|Ambiguous failure| L[Invalidate related caches safe-side]
    J -->|Non-ambiguous failure| M[Return ERR without inferred product state]
```

## 6. EB Event の扱い

```mermaid
stateDiagram-v2
    [*] --> EB_IDLE
    EB_IDLE --> EB_RECEIVE: EB frame detected
    EB_RECEIVE --> EB_VALIDATE: frame complete
    EB_VALIDATE --> EB_ACK: valid EB
    EB_VALIDATE --> EB_NAK: invalid EB
    EB_ACK --> EB_STORE_EVENT: decode current/change only
    EB_STORE_EVENT --> EB_IDLE: STATUS cache unchanged
    EB_NAK --> EB_IDLE: do not alter active transaction deadline
```

## 7. 遷移図作成時の注意
- NF55G Transaction は常に 1 件のみ。同時実行しない。
- Command Retry と Response Retry は別管理する。
- Pico から NF55G Response に対して送る NAK は plain `0x15` とし、Reason Code を付けない。
- Control Response 内の Status、D0 内の Status、EB Event で `STATUS` Cache を更新しない。
- D0 内の Manufacturing/Parameter を `INFO` Cache へ昇格しない。
- Partial Decode の結果を VALID Cache に保存しない。
- `FW_UPDATE` / `FU` は NF55G へ送信しない。

## 8. 参照仕様
- `AGENTS.md`
- `docs/Protocol_State_Machine.md`
- `docs/Software_Module_Interface.md`
- `docs/Cache_Master.md`
- `docs/ATE_Command_Master.md`
- `src/nf55_protocol.py`
