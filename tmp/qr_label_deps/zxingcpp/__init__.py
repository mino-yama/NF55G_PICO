# Re-export the native module for 'import zxingcpp' compatibility.
# Named init.py instead of __init__.py to avoid import conflicts when running from this directory.


# start delvewheel patch
def _delvewheel_patch_1_13_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'zxing_cpp.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_13_2()
del _delvewheel_patch_1_13_2
# end delvewheel patch

from .zxingcpp import *
