# 全体の入口：UART・RTC・SDと共通処理を組み立て、協調型ループで順番に処理する。
# ATE受信・応答を優先し、NF55G通信が落ち着いている間にRTC取得とログ保存を進める。

"""Fixture initialization and cooperative ATE/NF55G/SD scheduler."""

import binascii

# First application startup snapshot: RAM only, retained across SD_REINIT.
# Read from REPL after interrupting the loop, before resetting the interpreter.
startup_sd_diagnostic = None
active_app = None

try:
    from . import config
    from .external_instrument_contract import format_error
    from .external_instrument_link import ExternalInstrumentLink, new_nonce
    from .external_instrument_relay import RelayError
    from .ate_uart import create_ate_uart
    from .cache_manager import CacheManager
    from .calibration_measurement import CalibrationMeasurements, MeasurementError
    from .calibration_acquisition import CalibrationAcquisition, acquisition_id, measurement_reply
    from .calibration_write import SampleCalibrationWrite
    from .command_dispatcher import CommandDispatcher
    from .command_parser import ParseError, parse_ate_command
    from .diagnostic import FixtureDiagnostics
    from .logger import Logger
    from .nf55_protocol import NF55Protocol
    from .nf55_uart import create_nf55_uart
    from .rtc_driver import DS3231I2CDevice, DS3231RTC
    from .pico_clock import SystemClock
    from .ate_server import ATEServer
    from .sd_sink import PicoSDSink
    from .repl_sink import create_repl_sink
    from .qr_reader import QRReceiver, decode_qr
    from .qr_write_session import QRWriteSession, QRWriteError
    from .qr_reader import decode_nf55g_label
except ImportError:  # pragma: no cover
    import config
    from external_instrument_contract import format_error
    from external_instrument_link import ExternalInstrumentLink, new_nonce
    from external_instrument_relay import RelayError
    from ate_uart import create_ate_uart
    from cache_manager import CacheManager
    from calibration_measurement import CalibrationMeasurements, MeasurementError
    from calibration_acquisition import CalibrationAcquisition, acquisition_id, measurement_reply
    from calibration_write import SampleCalibrationWrite
    from command_dispatcher import CommandDispatcher
    from command_parser import ParseError, parse_ate_command
    from diagnostic import FixtureDiagnostics
    from logger import Logger
    from nf55_protocol import NF55Protocol
    from nf55_uart import create_nf55_uart
    from rtc_driver import DS3231I2CDevice, DS3231RTC
    from pico_clock import SystemClock
    from ate_server import ATEServer
    from sd_sink import PicoSDSink
    from repl_sink import create_repl_sink
    from qr_reader import QRReceiver, decode_qr
    from qr_write_session import QRWriteSession, QRWriteError
    from qr_reader import decode_nf55g_label


# ATEが終了応答を受け取ってから次の照会を返すまで、同期SD再認識を始めない。
SD_RECOVERY_IDLE_MS = 250


class FixtureApp:
    def __init__(self, ate_uart=None, nf55_uart=None, protocol=None, cache=None, logger=None, rtc=None, clock=None,
                 external_link=None, qr_transport=None, calibration_sample_enabled=False, qr_host_arm=False):
        self.clock = clock or getattr(protocol, 'clock', None) or SystemClock()
        self.external_link = external_link
        self.external_error = None
        self.external_response = None
        self._external_pending = False
        self._external_text = None
        self.ate_uart = ate_uart
        self.nf55_uart = nf55_uart
        self.protocol = protocol or (NF55Protocol(nf55_uart, clock=self.clock) if nf55_uart is not None else None)
        self.cache = cache or CacheManager(clock_ms=self.clock.ticks_ms)
        self.logger = logger or Logger(clock=self.clock, rtc=rtc)
        self.measurements = CalibrationMeasurements()
        self.calibration_acquisition = CalibrationAcquisition(self.measurements, external_link, self.clock)
        self.calibration_write = (SampleCalibrationWrite(self.measurements, self.protocol, self.cache, self.logger)
                                  if calibration_sample_enabled and self.protocol is not None else None)
        self._calibration_pending = False
        if self.logger.test_running:
            self.measurements.start_trial()
        self.rtc = rtc
        self.qr_reader = QRReceiver(on_ready=self.accept_qr)
        self.qr_write = QRWriteSession(self.clock, binascii.hexlify(new_nonce()).decode(), qr_transport, arm_host=qr_host_arm)
        if self.logger.test_running:
            self.qr_write.start_trial()
        self.server = ATEServer(ate_uart) if ate_uart is not None else None
        self.running = False
        self._last_rtc_sample = -1000
        self._sd_recovery_idle_since = None
        self.ate_error = None
        self.logger.busy = self._comm_busy
        if hasattr(self.logger.sd_sink, 'busy'):
            self.logger.sd_sink.busy = self._comm_busy
        if self.protocol is not None:
            # NF55G待ち時間にもATE入力を回収するが、別の要求はここでは実行しない。
            self.protocol.poll_hook = self._pump_ate
            self.protocol.trace_hook = self._trace_nf
        self.diagnostics = FixtureDiagnostics(rtc=self.rtc, logger=self.logger, ate_uart=self.ate_uart, nf55_uart=self.nf55_uart)
        self.dispatcher = CommandDispatcher(self.protocol, self.cache, logger=self.logger, rtc=self.rtc, diagnostics=self.diagnostics)

    def accept_qr(self, raw):
        # QR受信完了からのRAM連携口。NF55G書込みやSDアクセスは行わない。
        if not self.logger.test_running:
            return False
        try:
            fields = decode_nf55g_label(raw)
        except ValueError:
            self.logger.set_serial(None)
            return False
        accepted = self.logger.set_serial(fields['serial'])
        self.logger.log(category='QR', event='RECEIVED', result='OK' if accepted else 'INVALID_SN', detail=raw)
        return accepted

    def _comm_busy(self):
        if self._external_pending:
            return True
        if self.protocol is None:
            return False
        try:
            return self.protocol.communication_busy
        except OSError:
            return self.protocol.busy

    def _pump_ate(self):
        if self.server is not None:
            try:
                self.server.pump()
            except OSError as exc:
                self.ate_error = str(exc)

    def _trace_nf(self, direction, raw):
        # Only RAM operations. The timestamp is sampled outside communication.
        if self.logger.active:
            self.logger.log(category='NF55', direction=direction, event='RAW',
                            raw_hex=binascii.hexlify(raw).decode('ascii'),
                            detail='ticks_ms={}'.format(self.clock.ticks_ms()))

    def _record_result(self, result):
        tx = result.transaction
        if self.logger.active and tx is not None:
            self.logger.log(category='NF55', cmd=tx.cmd, event='TRANSACTION',
                            cmd_retry=tx.command_retry_count, rsp_retry=tx.response_retry_count,
                            result=result.ate_response,
                            detail='elapsed_ms={};ambiguous={}'.format(tx.elapsed_ms, tx.ambiguous))
        return result.ate_response

    def _service_external(self):
        if self.external_link is None:
            return
        if self._calibration_pending:
            # 校正取得中は取得処理だけがlinkをpollし、通常中継と競合させない。
            self.calibration_acquisition.poll()
            result = self.calibration_acquisition.take_result()
            if result is None:
                return
            self._calibration_pending = False
            reply = result['reply']
            if self.logger.active or self.logger.test_running:
                detail = acquisition_id(result['token'])
                if reply.startswith('OK:'):
                    detail = measurement_reply(self.measurements, result['token'])
                self.logger.log(category='CAL', event='ACQUIRED' if reply.startswith('OK:') else 'FAILED',
                                result=reply, detail=detail,
                                raw_hex=binascii.hexlify(result['raw'] or b'').decode('ascii'))
        else:
            self.external_link.poll()
            if not self._external_pending:
                return
            reply = self.external_link.take_reply()
            if reply is None:
                return
        self._external_pending = False
        if self.logger.active or self.logger.test_running:
            self.logger.log(category='ATE', direction='TX', event='RESULT', result=reply,
                            detail=self._external_text)
        if self.server is not None:
            try:
                self.server.reply(reply)
                self.server.flush_reply()
            except OSError as exc:
                self.ate_error = str(exc)
        else:
            self.external_response = reply

    def take_external_response(self):
        reply, self.external_response = self.external_response, None
        return reply

    # 1巡分の処理：ATE受信とidle EB処理→ATE応答/要求実行→空き時間のRTC/SD処理。
    def service_once(self):
        self._pump_ate()
        previous_qr = self.qr_write.state
        self.qr_write.poll()
        if previous_qr in ('ARMING', 'READING') and self.qr_write.state == 'READY':
            self.accept_qr(self.qr_write.raw)
        if self.protocol is not None:
            self.protocol.service_idle()
        self._service_external()
        if self.server is not None:
            try:
                if self.server.tx or self.server.pending:
                    self._sd_recovery_idle_since = None
                self.server.flush_reply()
                if not self.server.tx and self.server.pending and not self._comm_busy():
                    line, error = self.server.pending.pop(0)
                    if error:
                        response = 'ERR:' + error
                        # Parserへ渡せない受信異常も、試験中はRAM経由で記録する。
                        if self.logger.active or self.logger.test_running:
                            self.logger.log(category='ATE', direction='RX', event='RECEIVE_ERROR',
                                            raw_hex=binascii.hexlify(line).decode('ascii'), result=response,
                                            detail='retained prefix only; rejected by ATE transport')
                    else:
                        response = self.execute_ate_line(line)
                    if response is not None:
                        self.server.reply(response)
                        self.server.flush_reply()
                    # 最終応答の送出後は下のhas_work/busy判定へ進む。
                    # 常に次巡回へ延期すると、直後のATE burstでSD排出が飢餓状態になる。
                if self.server.has_work():
                    self._sd_recovery_idle_since = None
                    return
            except OSError as exc:
                self._sd_recovery_idle_since = None
                self.ate_error = str(exc)
                return
        if self._comm_busy():
            self._sd_recovery_idle_since = None
            return
        now = self.clock.ticks_ms()
        if self.rtc is not None and now - self._last_rtc_sample >= 1000:
            try:
                self.logger.timestamp_snapshot = self.rtc.datetime()
            except (ValueError, OSError):
                self.logger.timestamp_snapshot = ''
            self._last_rtc_sample = now
        self._service_sd_recovery()
        self.logger.service(protocol_busy=self._comm_busy())

    def _service_sd_recovery(self):
        # 通常のログ排出は延期せず、終了後の同期再認識だけを連続idleまで待たせる。
        if not self.logger.recovery_pending or self.logger.test_running or self.logger.active:
            self._sd_recovery_idle_since = None
            return
        if self.server is not None:
            now = self.clock.ticks_ms()
            if self._sd_recovery_idle_since is None:
                self._sd_recovery_idle_since = now
                return
            if now - self._sd_recovery_idle_since < SD_RECOVERY_IDLE_MS:
                return
            # RTC照会などの間に到着した入力も再認識の前に確認する。
            if self.server.has_work():
                self._sd_recovery_idle_since = None
                return
        self.logger.service_recovery()
        self._sd_recovery_idle_since = None

    def run(self):
        self.running = True
        try:
            while self.running:
                self.service_once()
                self.clock.sleep_ms(1)
        finally:
            self.running = False

    def stop(self):
        self.running = False

    def self_check(self):
        return self.diagnostics.pico_self_check()

    # 共通コマンド入口。分類ごとに担当へ渡し、NF55Gへ送らないローカル要求もここで分岐する。
    def execute_ate_line(self, line):
        # ATEの論理要求・実行結果をRAM記録する。TXはUART送信完了の意味ではない。
        was_recording = self.logger.active or self.logger.test_running
        previous_trial = self.logger.trial_id
        text = line.decode('ascii') if isinstance(line, bytes) and all(b < 128 for b in line) else str(line)
        if was_recording:
            self.logger.log(category='ATE', direction='RX', event='REQUEST', detail=text)
        response = self._execute_ate_line(line)
        new_trial = self.logger.trial_id != previous_trial
        if new_trial:
            # 前試行のQR・測定値・未完取得を新試行へ引き継がせない。
            self.qr_reader.cancel()
            self.qr_write.start_trial()
            self.measurements.start_trial()
            if self.calibration_write is not None:
                self.calibration_write.reset()
        if not self.logger.test_running:
            # 終了が通信/SD処理で延期された間は保持し、試行終了成立時に破棄する。
            self.measurements.end_trial()
            self.qr_write.end_trial()
            if self.calibration_write is not None:
                self.calibration_write.reset()
        if (not was_recording or new_trial) and (self.logger.active or self.logger.test_running):
            self.logger.log(category='ATE', direction='RX', event='REQUEST', detail=text)
        if response is not None and (self.logger.active or self.logger.test_running):
            self.logger.log(category='ATE', direction='TX', event='RESULT', result=response, detail=text)
        return response

    def _execute_ate_line(self, line):
        try:
            parsed = parse_ate_command(line)
        except (ParseError, UnicodeError) as exc:
            if isinstance(exc, UnicodeError):
                return 'ERR:ASCII'
            return "ERR:{}".format(exc)
        if parsed.category == "EXTERNAL":
            if self.external_link is None:
                return format_error('DISABLED', False)
            if self._comm_busy():
                return format_error('BUSY', False)
            try:
                self.external_link.start(parsed.payload)
            except RelayError as exc:
                return format_error(str(exc), False)
            self.external_response = None
            self._external_pending = True
            self._external_text = parsed.raw
            # 応答は協調型service_onceから返す。ここでUSB待ちを行わない。
            return None
        if parsed.category == "HOST_MANAGEMENT":
            if self.external_link is None:
                return "ERR:HOST_MANAGEMENT_DISABLED"
            if self._comm_busy():
                return "ERR:BUSY"
            try:
                self.external_link.start_management(parsed.payload)
            except RelayError as exc:
                return "ERR:HOST_{}".format(exc)
            self.external_response = None
            self._external_pending = True
            self._external_text = parsed.raw
            return None
        if parsed.category == "FORBIDDEN":
            return "ERR:FU_DISABLED"
        if self._external_pending:
            return "ERR:BUSY"
        if parsed.category == 'QR_WRITE_SESSION':
            return self._execute_qr(parsed.name, parsed.payload)
        if parsed.category == 'CALIBRATION_ACQUIRE':
            if self._comm_busy():
                return 'ERR:CAL_BUSY'
            try:
                self.calibration_acquisition.start(**parsed.payload)
            except MeasurementError as exc:
                return 'ERR:CAL_' + str(exc)
            self._external_pending = True
            self._calibration_pending = True
            self.external_response = None
            self._external_text = parsed.raw
            return None
        if parsed.category in ('CALIBRATION_QUERY', 'CALIBRATION_LATEST'):
            try:
                token = (self.measurements.latest_token(*parsed.payload)
                         if parsed.category == 'CALIBRATION_LATEST' else parsed.payload)
                reply = measurement_reply(self.measurements, token)
            except MeasurementError as exc:
                return 'ERR:CAL_' + str(exc)
            if self.calibration_write is not None:
                self.calibration_write.mark_queried(token)
            return reply
        if parsed.category == 'CALIBRATION_WRITE':
            # Cache採用と人の読取り値の直接指定は、同じ診断条件・単一通信制約で実行する。
            if self.calibration_write is None:
                return 'ERR:CAL_WRITE_DISABLED'
            if self._comm_busy():
                return 'ERR:BUSY'
            return self.calibration_write.execute(parsed.name, parsed.payload)
        if parsed.category == 'CALIBRATION_READBACK':
            if self.calibration_write is None:
                return 'ERR:CAL_READBACK_DISABLED'
            if self._comm_busy():
                return 'ERR:BUSY'
            return self.calibration_write.readback(*parsed.payload)
        if parsed.category == "REFRESH":
            return self._record_result(self.dispatcher.execute_refresh(parsed.name, parsed.payload))
        if parsed.category == "QUERY":
            return self.dispatcher.execute_query(parsed.name, parsed.payload).ate_response
        if parsed.category == "LOGGER":
            return self.dispatcher.execute_logger(parsed.name).ate_response
        if parsed.category == "RTC":
            return self.dispatcher.execute_rtc(parsed.name).ate_response
        if parsed.category == "DIAGNOSTIC":
            return self.dispatcher.execute_diagnostic(parsed.name).ate_response
        if parsed.category == "CONTROL":
            # 接続確認とBC開始時の旧結果無効化は共通Command Coreで処理する。
            return self._record_result(self.dispatcher.execute_control(parsed.name, payload=parsed.payload))
        return "ERR:UNKNOWN_CMD"

    def _execute_qr(self, name, token):
        try:
            if name == 'QR_CANCEL':
                self.qr_write.cancel()
                return 'OK'
            if name == 'QR_SCAN':
                acquisition = self.qr_write.start(token)
                response = 'OK:QR_PENDING:' if self.qr_write.arm_host else 'OK:QR_ARMED:'
                return response + acquisition
            if name in ('QR_GET?', 'QR_DATA?'):
                raw, data = self.qr_write.get(token, review=name == 'QR_DATA?')
                return 'OK:{}:{}:{}'.format(name[:-1], token,
                    raw if name == 'QR_GET?' else binascii.hexlify(data).decode())
            data = self.qr_write.write_data(token)
            if self._comm_busy():
                return 'ERR:QR_BUSY'
            if self.protocol is None:
                return 'ERR:NF55G_NOT_CONNECTED'
            # 送信前の条件拒否以外は再利用不可。成否不明もSSの失効規則へ。
            try:
                result = self.dispatcher.execute_control('SERIAL_SET_RAW', data)
            except OSError:
                self.cache.apply_ambiguous_invalidation('SS')
                self.logger.log(category='QR', event='WRITE', cmd='SS',
                                result='ERR:QR_WRITE:UART:AMBIGUOUS=1',
                                raw_hex=binascii.hexlify(data).decode(), detail='acquisition_id='+token)
                return 'ERR:QR_WRITE:UART:AMBIGUOUS=1'
            finally:
                self.qr_write.consume()
            response = self._record_result(result)
            self.logger.log(category='QR', event='WRITE', cmd='SS', result=response,
                            raw_hex=binascii.hexlify(data).decode(), detail='acquisition_id='+token)
            if result.transaction is not None and result.transaction.ambiguous:
                return 'ERR:QR_WRITE:{}:AMBIGUOUS=1'.format(result.error)
            return 'OK:QR_WRITE:'+token if result.ok else response
        except QRWriteError as exc:
            return 'ERR:QR_' + str(exc)


# 実機部品を生成して結合する。RTC/SDの初期化失敗は記録し、通信機能の起動を継続する。
def create_fixture_app(enable_hardware=True):
    global startup_sd_diagnostic
    clock = SystemClock()
    startup_started_ms = clock.ticks_ms()
    ate_uart = None
    nf55_uart = None
    rtc = None
    logger = None
    external_link = None
    external_error = None
    qr_transport = None
    if enable_hardware:
        if config.QR_HOST_ENABLED:
            try:
                from .qr_pio_rx import QRPioRx, QRPioUART
            except ImportError:
                from qr_pio_rx import QRPioRx, QRPioUART
            qr_port = QRPioUART if config.QR_HOST_ARM_ENABLED else QRPioRx
            qr_transport = qr_port(rx_pin=9, baudrate=115200, sm_id=0,
                                   tx_idle_pin=None, buffer_size=2048)
        if config.EXTERNAL_INSTRUMENT_ENABLED:
            transport = None
            try:
                try:
                    from .external_instrument_pio import ExternalPioUART
                except ImportError:
                    from external_instrument_pio import ExternalPioUART
                transport = ExternalPioUART()
                external_link = ExternalInstrumentLink(transport, clock, new_nonce(), config.EXTERNAL_HOST_CHIPID)
            except (ImportError, ValueError, OSError, RuntimeError, AttributeError) as exc:
                external_error = str(exc)
                if transport is not None:
                    transport.close()
        ate_uart = create_ate_uart()
        nf55_uart = create_nf55_uart()
        try:
            rtc = DS3231RTC(DS3231I2CDevice())
        except (ValueError, OSError):
            rtc = None
        sink = PicoSDSink()
        try:
            sink.mount()
        except (RuntimeError, OSError):
            pass  # Report SD status, keep ATE/NF55G available.
        if startup_sd_diagnostic is None:
            startup_sd_diagnostic = {
                'status': sink.status,
                'stage': sink.mount_stage,
                'error': sink.last_error,
                'mounted': sink.mounted,
                'startup_delay_ms': sink.startup_delay_ms,
                'cs_before_spi': sink.cs_before_spi,
                'elapsed_ms': clock.ticks_ms() - startup_started_ms,
            }
        logger = Logger(sd_sink=sink, clock=clock, rtc=rtc,
                repl_sink=create_repl_sink(config.REPL_LOG_ENABLED))
    app = FixtureApp(ate_uart=ate_uart, nf55_uart=nf55_uart, rtc=rtc, logger=logger, clock=clock,
                     external_link=external_link, qr_transport=qr_transport,
                     calibration_sample_enabled=config.CALIBRATION_SAMPLE_ENABLED,
                     qr_host_arm=config.QR_HOST_ARM_ENABLED)
    app.external_error = external_error
    return app


def main():
    global active_app
    active_app = create_fixture_app(enable_hardware=True)
    active_app.run()


if __name__ == "__main__":  # pragma: no cover
    main()
