#include <sys/reent.h>
#include "pico/mutex.h"

auto_init_recursive_mutex(external_meter_newlib_malloc_mutex);

void __malloc_lock(struct _reent *reent) {
    (void)reent;
    recursive_mutex_enter_blocking(&external_meter_newlib_malloc_mutex);
}

void __malloc_unlock(struct _reent *reent) {
    (void)reent;
    recursive_mutex_exit(&external_meter_newlib_malloc_mutex);
}