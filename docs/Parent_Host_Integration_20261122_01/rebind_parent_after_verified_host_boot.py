# 実機診断用のRAM再初期化。public APIや量産の自動fault解除ではない。
# 新Host起動をHで確認し、そのbootにQ未送信・親要求なしの場合だけ使用する。
import binascii
from src.external_instrument_link import ExternalInstrumentLink

old_link = app.external_link
assert not app._external_pending
assert not old_link.busy
assert old_link.session is None
assert old_link.core._sequence == 0
assert not app.logger.active
assert not app._comm_busy()
assert binascii.hexlify(old_link.parent_nonce).decode() == 'aebff8cd13a17ffe'
app.external_link = ExternalInstrumentLink(old_link.transport, old_link.clock,
                                           old_link.parent_nonce, old_link.expected_chipid)
print('PARENT_ADAPTER_REINITIALIZED same_parent_nonce=1 no_Q_on_new_Host_boot=1')
