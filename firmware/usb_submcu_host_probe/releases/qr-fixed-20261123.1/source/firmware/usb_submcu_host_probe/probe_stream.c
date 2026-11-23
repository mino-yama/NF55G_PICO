// UARTへ排出済みの領域を再利用する。満杯時は上書きせず欠落数を残す。
#include "probe_stream.h"
#include <string.h>
typedef char probe_record_abi_must_be_76[(sizeof(probe_record_t)==76)?1:-1];
void probe_stream_init(probe_stream_t *s) { memset(s,0,sizeof(*s)); }
bool probe_stream_push(probe_stream_t *s, const probe_record_t *r) {
 if(s->count==PROBE_STREAM_CAPACITY) { s->dropped++; return false; }
 s->records[s->head]=*r;
 s->head=(s->head+1)%PROBE_STREAM_CAPACITY; s->count++;
 return true;
}
bool probe_stream_pop(probe_stream_t *s, probe_record_t *r) {
 if(!s->count) return false;
 *r=s->records[s->tail];
 s->tail=(s->tail+1)%PROBE_STREAM_CAPACITY; s->count--;
 return true;
}
