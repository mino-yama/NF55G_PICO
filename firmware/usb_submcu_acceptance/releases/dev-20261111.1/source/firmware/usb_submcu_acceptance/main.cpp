// USB SubMCUの初回確認専用。Type_C1のUSB CDCだけを初期化する。
// USB Host/PIO/UART/LED/SD/RTCは起動せず、製品向け指令は扱わない。
#include <cstdio>
#include <cstring>
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"
#include "pico/unique_id.h"
#include "pico/version.h"
static constexpr char kVersion[] = "dev-20261111.1";
static constexpr size_t kMaxLine = 95;
static void reply(const char *line, const char *id) {
    if (std::strcmp(line, "ID?") == 0) {
        std::printf("FW=USB_SUBMCU_ACCEPTANCE;VERSION=%s;BUILD=%s;SDK=%s;"
                    "BOARD=RP2350_USB_C;ID=%s;USB_HOST=OFF;UART=OFF;PIO=OFF\r\n",
                    kVersion, ACCEPTANCE_BUILD_ID, PICO_SDK_VERSION_STRING, id);
    } else if (std::strcmp(line, "PING") == 0) {
        std::printf("PONG\r\n");
    } else if (std::strcmp(line, "UPTIME?") == 0) {
        std::printf("UPTIME_MS=%llu\r\n",
                    static_cast<unsigned long long>(to_ms_since_boot(get_absolute_time())));
    } else if (std::strncmp(line, "ECHO ", 5) == 0) {
        std::printf("ECHO=%s\r\n", line + 5);
    } else {
        std::printf("ERR:UNKNOWN_CMD\r\n");
    }
}
int main() {
    char id[PICO_UNIQUE_BOARD_ID_SIZE_BYTES * 2 + 1];
    pico_get_unique_board_id_string(id, sizeof(id));
    if (!stdio_usb_init()) {
        while (true) { sleep_ms(100); }
    }
    stdio_set_translate_crlf(&stdio_usb, false);
    char line[kMaxLine + 1] = {};
    size_t used = 0;
    bool dropping = false;
    const char *error = nullptr;
    bool connected = false;
    while (true) {
        const bool now_connected = stdio_usb_connected();
        if (!now_connected) {
            // 接続終了時に部分行を失効させ、次のセッションへ持ち越さない。
            used = 0;
            dropping = false;
            error = nullptr;
            connected = false;
            sleep_ms(1);
            continue;
        }
        if (!connected) {
            std::printf("READY:USB_SUBMCU_ACCEPTANCE\r\n");
            connected = true;
        }
        const int value = getchar_timeout_us(0);
        if (value == PICO_ERROR_TIMEOUT) {
            sleep_ms(1);
            continue;
        }
        if (value == '\r' || value == '\n') {
            // CR/LF/CRLFを受理し、空行を無視する。内部UARTの仕様ではない。
            if (dropping) {
                std::printf("%s\r\n", error);
            } else if (used != 0) {
                line[used] = '\0';
                reply(line, id);
            }
            used = 0;
            dropping = false;
            error = nullptr;
        } else if (!dropping) {
            // 不正文字・過長行は終端まで破棄し、部分指令を実行しない。
            if (value < 32 || value > 126) {
                dropping = true;
                error = "ERR:ASCII";
            } else if (used == kMaxLine) {
                dropping = true;
                error = "ERR:LINE_TOO_LONG";
            } else {
                line[used++] = static_cast<char>(value);
            }
        }
    }
}
