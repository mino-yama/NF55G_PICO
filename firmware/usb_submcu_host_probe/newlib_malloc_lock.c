// Arduino GCC14.3同梱newlibのmallocロックをSDKの再帰mutexへ接続する。
// newlib公開hookを実装し、ロックをno-opにする回避策は使わない。
#include <sys/reent.h>
#include "pico/mutex.h"
auto_init_recursive_mutex(probe_newlib_malloc_mutex);
void __malloc_lock(struct _reent *reent) {
 (void)reent;
 recursive_mutex_enter_blocking(&probe_newlib_malloc_mutex);
}
void __malloc_unlock(struct _reent *reent) {
 (void)reent;
 recursive_mutex_exit(&probe_newlib_malloc_mutex);
}
