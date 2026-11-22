# 検証済み新Host bootへ切替える保守試験専用RAM処理。量産APIではない。
# H以外のQを新Hostへ送っていない段階でだけ使い、旧Host世代のfaultを持ち越さない。
from src.external_instrument_link import ExternalInstrumentLink
import binascii

old_link = app.external_link
assert probe_ready_samples >= 3
assert verified_host_session[:8] == old_link.parent_nonce
assert old_link.session is not None
assert verified_host_session[8:] != old_link.session[8:]
assert not old_link.busy and not app._external_pending
assert not app._comm_busy() and not app.logger.active
assert old_link.transport.take_error() is None
app.external_link = ExternalInstrumentLink(old_link.transport, old_link.clock,
                                           old_link.parent_nonce, old_link.expected_chipid)
print('ADAPTER_REINITIALIZED_NEW_HOST=' + binascii.hexlify(verified_host_session[8:]).decode())
