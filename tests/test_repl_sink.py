import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.logger import CSV_FIELDS, Logger, MemorySDSink
from src.mock_nf55g import FakeClock
from src.repl_sink import ReplDebugSink, create_repl_sink
from src.sd_sink import csv_line


class FakeStream:
    def __init__(self):
        self.output = []

    def write(self, text):
        self.output.append(text)
        return len(text)


class FakePoller:
    def __init__(self):
        self.stream = None
        self.event = 0

    def register(self, stream, _events):
        self.stream = stream

    def poll(self, _timeout):
        return [(self.stream, self.event)] if self.event else []


class ReplDebugSinkTests(unittest.TestCase):
    def make_sink(self, **kwargs):
        stream = FakeStream()
        poller = FakePoller()
        sink = ReplDebugSink(stream=stream, poller=poller, **kwargs)
        return sink, stream, poller

    def test_waits_for_writable_stream_and_sends_bounded_chunks(self):
        sink, stream, poller = self.make_sink(chunk_size=4)
        row = ("", "ATE", "RX", "", "REQUEST", "", "", "", "", "", "", "", "", "*IDN?")
        self.assertTrue(sink.write_record(row))

        self.assertEqual(sink.service(), 0)
        self.assertEqual(stream.output, [])

        poller.event = 4
        self.assertEqual(sink.service(), 4)
        self.assertEqual(stream.output, [csv_line(row)[:4]])
        self.assertGreater(sink.pending_bytes, 0)

    def test_start_queues_the_same_csv_header(self):
        sink, _stream, _poller = self.make_sink()

        sink.start()

        self.assertEqual(sink.queue, [(csv_line(CSV_FIELDS), 0)])

    def test_full_queue_drops_repl_copy_only(self):
        sink, _stream, _poller = self.make_sink(queue_limit=1)

        self.assertFalse(sink.write_record(("record",)))
        self.assertEqual(sink.drop_count, 1)
        self.assertEqual(sink.queue, [])

    def test_disconnect_drops_pending_copy_and_disables_sink(self):
        sink, _stream, poller = self.make_sink()
        self.assertTrue(sink.write_record(("record",)))
        poller.event = sink.poll_errors & -sink.poll_errors

        self.assertEqual(sink.service(), 0)

        self.assertFalse(sink.enabled)
        self.assertEqual(sink.queue, [])
        self.assertEqual(sink.drop_count, 1)

    def test_sink_factory_can_disable_repl_mirror(self):
        self.assertIsNone(create_repl_sink(False))
        self.assertIsInstance(create_repl_sink(True), ReplDebugSink)

    def test_logger_mirrors_the_sd_written_csv_row(self):
        repl, stream, poller = self.make_sink(chunk_size=32)
        sd = MemorySDSink()
        logger = Logger(sd_sink=sd, clock=FakeClock(), repl_sink=repl, flush_record_count=1)
        row = ("", "ATE", "RX", "", "REQUEST", "", "", "", "", "", "", "", "", "*IDN?")
        self.assertTrue(logger.test_start())
        logger.log(category="ATE", direction="RX", event="REQUEST", detail="*IDN?")
        filename = logger.current_filename

        poller.event = 4
        self.assertEqual(logger.service(), 1)
        while repl.queue:
            repl.service()

        self.assertEqual(sd.files[filename][0], row)
        self.assertEqual("".join(stream.output), csv_line(CSV_FIELDS) + csv_line(row))

    def test_logger_skips_repl_output_while_protocol_busy(self):
        repl, stream, poller = self.make_sink()
        logger = Logger(sd_sink=MemorySDSink(), clock=FakeClock(), repl_sink=repl)
        self.assertTrue(logger.test_start())
        logger.log(category="ATE", detail="request")
        poller.writable = True

        self.assertEqual(logger.service(protocol_busy=True), 0)

        self.assertEqual(stream.output, [])
        self.assertEqual(logger.sd_sink.write_count, 0)


if __name__ == "__main__":
    unittest.main()