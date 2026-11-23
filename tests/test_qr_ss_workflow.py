"""実C側と同じ診断レコードから明示SS・Cache失効・D5までを検証する。"""
import struct
import unittest
from src.frame import parse_frame
from src.main import FixtureApp
from src.mock_nf55g import FakeClock, MockUART, MockNF55GScenario, ScenarioStep
from src.nf55_protocol import NF55Protocol
from src.qr_write_session import serial_data_from_qr
from tests.test_runtime_integration import BytePort

QR='US250A-CGXE-009491-101A1.2601000001'
OTHER=QR[:-6]+'000002'


def record(seq, raw=QR, kind=12):
    data=raw.encode() if isinstance(raw,str) else raw
    return b'@'+struct.pack('<IIBBBB64s',seq,seq*100,kind,1,0,len(data),data).hex().encode()+b'\n'


class QRPort(BytePort):
    fault=None
    def take_error(self):
        fault,self.fault=self.fault,None
        return fault


class QRSSWorkflowTests(unittest.TestCase):
    def make(self, steps=()):
        clock=FakeClock()
        uart=MockUART(clock,MockNF55GScenario(steps))
        qr=QRPort()
        app=FixtureApp(protocol=NF55Protocol(uart,clock),clock=clock,qr_transport=qr)
        self.assertEqual(app.execute_ate_line('TEST_START'),'OK')
        return app,uart,qr,clock

    def acquire(self, app, qr, wire=None):
        response=app.execute_ate_line('QR_SCAN 10000')
        self.assertTrue(response.startswith('OK:QR_ARMED:'),response)
        token=response.split(':')[-1]
        qr.rx.extend(record(100)+record(101,OTHER) if wire is None else wire)
        app.service_once()
        return token

    def review(self, app, token):
        result=app.execute_ate_line('QR_DATA? '+token)
        self.assertTrue(result.startswith('OK:QR_DATA:'),result)
        return bytes.fromhex(result.split(':')[-1])

    def frames(self, uart):
        return [parse_frame(x) for x in uart.tx_log if x.startswith(b'\2')]

    def test_two_scans_freeze_first_then_one_explicit_ss_and_readback(self):
        d5=b'S1.14B'+b'A1. '+b'2601'+b'000001'+b'0'*30+b'0'*50
        app,uart,qr,_=self.make([ScenarioStep.ack_response('SS'),ScenarioStep.ack_response('D5',d5)])
        token=self.acquire(app,qr)
        self.assertEqual(app.qr_write.ignored,1)
        self.assertEqual(app.execute_ate_line('QR_GET? '+token),'OK:QR_GET:'+token+':'+QR)
        data=self.review(app,token)
        self.assertEqual(data,b'FFFFFFA1. 2601000001'+b'F'*30)
        self.assertEqual(self.frames(uart),[])
        for name in ('DATA','STATUS','INFO'):
            app.cache.validate(name,{'old':True},'TEST')
        self.assertEqual(app.execute_ate_line('QR_WRITE '+token),'OK:QR_WRITE:'+token)
        self.assertFalse(app.cache.is_valid('DATA'));self.assertFalse(app.cache.is_valid('INFO'))
        self.assertTrue(app.cache.is_valid('STATUS'))
        self.assertTrue(app.execute_ate_line('QR_WRITE '+token).startswith('ERR:'))
        self.assertEqual(app.execute_ate_line('UNIT_SERIAL?'),'ERR:CACHE_INVALID')
        self.assertEqual(len(self.frames(uart)),1)
        self.assertEqual(self.frames(uart)[0].data,data)
        self.assertEqual(app.execute_ate_line('INFO_REFRESH'),'OK')
        self.assertEqual(app.execute_ate_line('UNIT_REV?'),'A1. ')
        self.assertEqual(app.execute_ate_line('UNIT_SERIAL?'),'000001')
        self.assertEqual([f.cmd for f in self.frames(uart)],['SS','D5'])

    def test_write_requires_query_and_correct_id_without_transmission(self):
        app,uart,qr,_=self.make()
        token=self.acquire(app,qr)
        self.assertEqual(app.execute_ate_line('QR_WRITE '+token),'ERR:QR_NOT_REVIEWED')
        self.review(app,token)
        self.assertTrue(app.execute_ate_line('QR_WRITE '+token+'0').startswith('ERR:'))
        self.assertEqual(self.frames(uart),[])

    def test_timeout_uart_drop_frame_and_host_error_never_write(self):
        wires=(b'broken\n',record(1,b'\7',13),record(1,b'',1),record(1,b'',3),
               record(1,struct.pack('<6I',1,1,0,0,0,128),14),
               record(1,struct.pack('<6I',1,1,1,0,0,13),14),
               record(1,'A'*34),record(1,b'',15)+record(3))
        for wire in wires:
            with self.subTest(wire=wire):
                app,uart,qr,_=self.make()
                token=self.acquire(app,qr,wire)
                self.assertEqual(app.qr_write.state,'ERROR')
                self.assertTrue(app.execute_ate_line('QR_WRITE '+token).startswith('ERR:'))
                self.assertEqual(self.frames(uart),[])
        app,uart,qr,clock=self.make()
        token=app.execute_ate_line('QR_SCAN 100').split(':')[-1]
        clock.sleep_ms(101);qr.rx.extend(record(0));app.service_once()
        self.assertEqual(app.qr_write.error,'TIMEOUT')
        self.assertEqual(self.frames(uart),[])

    def test_old_buffer_cancel_trial_end_and_new_trial_cannot_reuse(self):
        app,uart,qr,_=self.make()
        qr.rx.extend(record(1))
        token=app.execute_ate_line('QR_SCAN 10000').split(':')[-1]
        app.service_once();self.assertEqual(app.qr_write.state,'READING')
        self.assertEqual(app.execute_ate_line('QR_CANCEL'),'OK')
        qr.rx.extend(record(2));app.service_once()
        self.assertTrue(app.execute_ate_line('QR_DATA? '+token).startswith('ERR:'))
        token=self.acquire(app,qr);self.review(app,token)
        app.qr_write.end_trial()
        self.assertTrue(app.execute_ate_line('QR_WRITE '+token).startswith('ERR:'))
        app.qr_write.start_trial()
        self.assertTrue(app.execute_ate_line('QR_WRITE '+token).startswith('ERR:'))
        self.assertEqual(self.frames(uart),[])

    def test_ambiguous_ss_consumes_snapshot_and_invalidates(self):
        app,uart,qr,_=self.make([ScenarioStep.ack_timeout(),ScenarioStep.ack_timeout()])
        token=self.acquire(app,qr);self.review(app,token)
        for name in ('DATA','INFO'):
            app.cache.validate(name,{},'TEST')
        result=app.execute_ate_line('QR_WRITE '+token)
        self.assertIn('AMBIGUOUS=1',result)
        self.assertFalse(app.cache.is_valid('INFO'));self.assertFalse(app.cache.is_valid('DATA'))
        self.assertEqual(app.qr_write.state,'CONSUMED')
        count=len(self.frames(uart))
        self.assertTrue(app.execute_ate_line('QR_WRITE '+token).startswith('ERR:'))
        self.assertEqual(len(self.frames(uart)),count)

    def test_busy_and_no_protocol_do_not_consume_unsent_snapshot(self):
        app,uart,qr,_=self.make()
        token=self.acquire(app,qr);self.review(app,token)
        app.protocol.busy=True
        self.assertEqual(app.execute_ate_line('QR_WRITE '+token),'ERR:QR_BUSY')
        app.protocol=None
        self.assertEqual(app.execute_ate_line('QR_WRITE '+token),'ERR:NF55G_NOT_CONNECTED')
        self.assertEqual(app.qr_write.state,'READY')
        self.assertEqual(self.frames(uart),[])

    def test_strict_arguments_fu_and_no_public_raw_ss(self):
        app,uart,qr,_=self.make()
        for request in ('QR_SCAN','QR_SCAN 99','QR_SCAN 60001','QR_SCAN -1','QR_SCAN 100 extra',
                        'QR_WRITE','QR_DATA? invalid','QR_CANCEL extra','SERIAL_SET_RAW '+('0'*50)):
            self.assertTrue(app.execute_ate_line(request).startswith('ERR:'),request)
        self.assertEqual(app.execute_ate_line('FW_UPDATE'),'ERR:FU_DISABLED')
        self.assertEqual(self.frames(uart),[])

    def test_actual_mapping_does_not_fix_model_or_revision(self):
        raw='XS999Z-Q'+'ABC-123456-999'+'B2.'+'2753'+'123456'
        data=serial_data_from_qr(raw)
        self.assertEqual(data[6:20],b'B2. 2753123456')
        self.assertEqual(len(data),50)

    def test_transport_exception_consumes_and_invalidates(self):
        app,uart,qr,_=self.make()
        token=self.acquire(app,qr);self.review(app,token)
        for name in ('DATA','INFO','STATUS'):
            app.cache.validate(name,{},'TEST')
        def fail(*args,**kwargs):
            raise OSError('UART')
        app.protocol.transact=fail
        self.assertIn('AMBIGUOUS=1',app.execute_ate_line('QR_WRITE '+token))
        self.assertEqual(app.qr_write.state,'CONSUMED')
        self.assertFalse(app.cache.is_valid('INFO'));self.assertTrue(app.cache.is_valid('STATUS'))

    def test_trial_commands_invalidate_old_acquisition(self):
        app,uart,qr,_=self.make()
        token=self.acquire(app,qr);self.review(app,token)
        self.assertEqual(app.execute_ate_line('TEST_END'),'OK')
        self.assertTrue(app.execute_ate_line('QR_WRITE '+token).startswith('ERR:'))
        self.assertEqual(app.execute_ate_line('TEST_START'),'OK')
        self.assertTrue(app.execute_ate_line('QR_WRITE '+token).startswith('ERR:'))
        new=self.acquire(app,qr)
        self.assertNotEqual(token,new)
        self.assertEqual(self.frames(uart),[])

    def test_receiver_fault_and_fragmented_records(self):
        app,uart,qr,_=self.make()
        token=app.execute_ate_line('QR_SCAN 10000').split(':')[-1]
        raw=record(1)
        for byte in raw:
            qr.rx.append(byte);app.service_once()
        self.assertEqual(app.qr_write.state,'READY')
        self.assertEqual(app.execute_ate_line('QR_GET? '+token),'OK:QR_GET:'+token+':'+QR)
        app.execute_ate_line('QR_SCAN 10000')
        qr.fault='QR_RX_OVERFLOW';app.service_once()
        self.assertEqual(app.qr_write.state,'ERROR')
        self.assertEqual(self.frames(uart),[])
