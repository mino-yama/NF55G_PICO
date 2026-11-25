"""Time one post-trial SD recovery in RAM on the identified parent Pico."""

import binascii
import machine
import sys

assert binascii.hexlify(machine.unique_id()).decode() == '69f7d45962cfdfad'
app = sys.modules['src.main'].active_app
logger = app.logger
assert logger.active and logger.test_running and logger.trial_id == 'T000320'
assert not app._comm_busy() and not app.external_link.fault
original_reinit = logger.reinit


def timed_reinit():
    started = app.clock.ticks_ms()
    print('SD_RECOVERY_START', started)
    try:
        return original_reinit()
    finally:
        print('SD_RECOVERY_END', app.clock.ticks_ms() - started, logger.sd_status,
              logger.sd_sink.mount_stage, logger.sd_sink.last_error)
        logger.reinit = original_reinit


logger.reinit = timed_reinit
print('PARENT_RESUMED_FOR_TEST_END', logger.trial_id)
app.run()
