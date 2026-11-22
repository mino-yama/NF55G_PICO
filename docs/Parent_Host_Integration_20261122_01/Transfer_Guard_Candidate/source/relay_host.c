#include "relay_host.h"
#include <stdio.h>
#include <string.h>

// 固定SDKのZLP完了callbackを次の送信データ完了と誤認しないよう奇数長に分割する。
size_t relay_usb_chunk_size(size_t remaining) {
    size_t size = remaining > 63u ? 63u : remaining;
    return size > 0u && (size & 1u) == 0u ? size - 1u : size;
}

static bool emit_frame(relay_host_t *host, const x1_frame_t *frame) {
    if (host->emit(host->context, frame)) return true;
    host->fault = true;
    host->pending = false;
    return false;
}

static bool event(relay_host_t *host, char kind, const uint8_t *payload, size_t length) {
    x1_frame_t frame = host->request;
    frame.kind = kind;
    frame.length = (uint16_t)length;
    if (length > 0u) memcpy(frame.payload, payload, length);
    return emit_frame(host, &frame);
}

static void error_frame(relay_host_t *host, const x1_frame_t *request, const char *reason, bool ambiguous) {
    x1_frame_t frame = *request;
    frame.kind = 'E';
    int length = snprintf((char *)frame.payload, sizeof(frame.payload), "%s|%u", reason, ambiguous ? 1u : 0u);
    if (length <= 0 || (size_t)length >= sizeof(frame.payload)) {
        host->fault = true;
        host->pending = false;
        return;
    }
    frame.length = (uint16_t)length;
    emit_frame(host, &frame);
}

void relay_host_fail(relay_host_t *host, const char *reason) {
    host->fault = true;
    if (host->pending) error_frame(host, &host->request, reason, host->tx_started);
    host->pending = false;
}

void relay_host_init(relay_host_t *host, const uint8_t nonce[8], const char *chipid,
                     const char *version, relay_emit_fn emit, void *context) {
    memset(host, 0, sizeof(*host));
    memcpy(host->nonce, nonce, 8u);
    host->chipid = chipid;
    host->version = version;
    host->emit = emit;
    host->context = context;
}

void relay_host_device_ready(relay_host_t *host, bool ready) {
    if (!ready && host->pending) {
        // CDC送信開始後は成否不明として停止、未送信なら明示拒否して次の要求を妨げない。
        if (host->tx_started) {
            relay_host_fail(host, "DISCONNECTED");
        } else {
            error_frame(host, &host->request, "LINK_NOT_READY", false);
            host->pending = false;
        }
    }
    host->ready = ready;
}

static bool zeroes(const uint8_t *data, size_t length) {
    for (size_t i = 0u; i < length; i++) if (data[i] != 0u) return false;
    return true;
}

static void hello(relay_host_t *host, const x1_frame_t *request) {
    if (request->request != 0u || request->mode != 0u || request->timeout_ms != 0u ||
        request->length != 0u || zeroes(request->session, 8u) || !zeroes(request->session + 8u, 8u)) return;
    if (host->bound && memcmp(request->session, host->session, 8u) != 0) relay_host_fail(host, "PARENT_RESTART");
    x1_frame_t reply = *request;
    memcpy(reply.session + 8u, host->nonce, 8u);
    reply.kind = 'h';
    const char *state = host->fault ? "FAULT" : host->pending ? "BUSY" : host->ready ? "READY" : "NOT_READY";
    int size = snprintf((char *)reply.payload, sizeof(reply.payload), "%s|%s|%s", host->chipid, host->version, state);
    if (size <= 0 || (size_t)size >= sizeof(reply.payload)) { host->fault = true; return; }
    reply.length = (uint16_t)size;
    if (!host->bound && host->ready && !host->fault) {
        memcpy(host->session, reply.session, 16u);
        host->bound = true;
    }
    emit_frame(host, &reply);
}

static void accept_request(relay_host_t *host, const x1_frame_t *request, uint32_t now) {
    if (request->kind == 'H') { hello(host, request); return; }
    if (request->kind != 'Q' || !host->bound || memcmp(request->session, host->session, 16u) != 0) return;
    if (host->fault) { error_frame(host, request, "RECOVERY_REQUIRED", false); return; }
    if (!host->ready) { error_frame(host, request, "LINK_NOT_READY", false); return; }
    if (request->request <= host->high_watermark) {
        if (host->pending) relay_host_fail(host, "REPLAY_REQUEST");
        else error_frame(host, request, "REPLAY_REQUEST", false);
        return;
    }
    if (host->pending) { error_frame(host, request, "BUSY", false); return; }
    if (request->request == 0u || request->timeout_ms == 0u || request->length == 0u) {
        error_frame(host, request, "REQUEST_FORMAT", false); return;
    }
    for (size_t i = 0u; i < request->length; i++) {
        if (request->payload[i] < 32u || request->payload[i] > 126u) {
            error_frame(host, request, "COMMAND_ASCII", false); return;
        }
    }
    host->request = *request;
    host->high_watermark = request->request;
    host->started_at = now;
    host->pending = true;
    host->tx_started = false;
    host->tx_done = false;
    host->response_done = false;
    host->response_length = 0u;
    host->command_length = request->length + 2u;
    memcpy(host->command, request->payload, request->length);
    host->command[request->length] = '\r';
    host->command[request->length + 1u] = '\n';
    event(host, 'A', NULL, 0u);
}

void relay_host_poll(relay_host_t *host, uint32_t now) {
    if (host->pending && (uint32_t)(now - host->started_at) >= host->request.timeout_ms)
        relay_host_fail(host, "TIMEOUT");
}

void relay_host_uart(relay_host_t *host, const uint8_t *data, size_t length, uint32_t now) {
    relay_host_poll(host, now);
    for (size_t i = 0u; i < length; i++) {
        uint8_t value = data[i];
        // 起動時の余分なbyteをHへ連結しない。payloadはHEXなので@は先頭にしか現れない。
        // 再同期後も全体のCRC/長さ/session検証を通す。再送やfault解除は行わない。
        if (value == '@') {
            if (host->uart_length > 0u || host->uart_drop) host->rejected_frames++;
            host->uart_length = 0u;
            host->uart_drop = false;
            host->previous = 0u;
        }
        if (host->uart_drop || (host->uart_length == 0u && value != '@')) continue;
        if (host->uart_length >= sizeof(host->uart)) {
            host->uart_length = 0u;
            host->uart_drop = true;
            host->previous = 0u;
            host->rejected_frames++;
            continue;
        }
        host->uart[host->uart_length++] = value;
        if (host->previous == '\r' && value == '\n') {
            x1_frame_t frame;
            if (!host->uart_drop && x1_decode(host->uart, host->uart_length, &frame)) accept_request(host, &frame, now);
            else host->rejected_frames++;
            host->uart_length = 0u;
            host->uart_drop = false;
        }
        host->previous = value;
    }
}

void relay_host_tx_started(relay_host_t *host) {
    if (host->pending) host->tx_started = true;
}

static void complete_response(relay_host_t *host) {
    if (host->pending && host->tx_done && host->response_done) {
        event(host, 'R', host->response, host->response_length);
        host->pending = false;
    }
}

void relay_host_tx_done(relay_host_t *host) {
    if (!host->pending || !host->tx_started || host->tx_done) return;
    host->tx_done = true;
    if (!event(host, 'T', NULL, 0u)) return;
    if (host->request.mode == 0u) host->pending = false;
    else complete_response(host);
}

void relay_host_rx(relay_host_t *host, const uint8_t *data, size_t length, uint32_t now) {
    relay_host_poll(host, now);
    if (length == 0u) return;
    if (!host->pending || !host->tx_started || host->request.mode == 0u) {
        relay_host_fail(host, "UNEXPECTED_DATA"); return;
    }
    if (host->response_length + length > sizeof(host->response)) {
        relay_host_fail(host, "RESPONSE_TOO_LONG"); return;
    }
    if (host->response_done) { relay_host_fail(host, "EXTRA_DATA"); return; }
    memcpy(host->response + host->response_length, data, length);
    host->response_length += length;
    for (size_t i = 1u; i < host->response_length; i++) {
        if (host->response[i - 1u] == '\r' && host->response[i] == '\n') {
            if (i + 1u != host->response_length) relay_host_fail(host, "EXTRA_DATA");
            else { host->response_done = true; complete_response(host); }
            return;
        }
    }
}
