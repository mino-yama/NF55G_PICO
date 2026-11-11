# RAM-only identification; no GPIO/peripheral or filesystem writes.
import sys
import os
print('SUBMCU_ID_BEGIN')
print(sys.implementation)
print(sys.version)
print(os.uname())
print(os.listdir('/'))
print('SUBMCU_ID_END')
