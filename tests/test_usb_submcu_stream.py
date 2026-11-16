"""実機と同じC FIFOとデコーダで周回・欠落・連続読取を検証する。"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include "probe_stream.h"
#include "qr_alt_decoder.h"
#include <assert.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
 assert(argc==2);
 probe_stream_t q; probe_stream_init(&q);
 probe_record_t r={0},out={0};
 int mode=atoi(argv[1]);
 if(mode==1) {
  for(unsigned base=0;base<10000;base+=40) {
   for(unsigned i=0;i<40;i++) { r.seq=base+i; r.length=64; memset(r.data,i,64); assert(probe_stream_push(&q,&r)); }
   for(unsigned i=0;i<40;i++) { assert(probe_stream_pop(&q,&out)); assert(out.seq==base+i && out.data[63]==i && out.length==64); }
  }
  assert(q.count==0 && q.dropped==0);
 } else if(mode==2) {
  for(unsigned i=0;i<64;i++) { r.seq=i; assert(probe_stream_push(&q,&r)); }
  for(unsigned i=0;i<3;i++) { r.seq=999; assert(!probe_stream_push(&q,&r)); }
  assert(q.dropped==3 && q.count==64);
  for(unsigned i=0;i<64;i++) { assert(probe_stream_pop(&q,&out)); assert(out.seq==i); }
  r.seq=1000; assert(probe_stream_push(&q,&r)); assert(probe_stream_pop(&q,&out) && out.seq==1000);
  assert(q.dropped==3);
 } else if(mode==3) {
  out.seq=123; assert(!probe_stream_pop(&q,&out)); assert(out.seq==123);
  probe_stream_init(&q); assert(q.count==0 && q.dropped==0);
 } else if(mode==4) {
  qr_alt_decoder_t d; qr_alt_decoder_init(&d);
  uint32_t now=0; unsigned emitted=0;
  for(unsigned scan=0;scan<200;scan++) {
   char wanted[36],text[36]; memset(wanted,scan%2?'Z':'0',35); wanted[35]=0;
   for(unsigned c=0;c<35;c++) {
    unsigned value=(unsigned)wanted[c],div=10000;
    for(unsigned j=0;j<5;j++,div/=10) {
     unsigned digit=(value/div)%10;
     uint8_t rep[8]={4,0,(uint8_t)(digit?0x58+digit:0x62)};
     assert(qr_alt_decoder_feed(&d,rep,8,now+=3,text)==QR_ALT_NONE);
     rep[2]=0; assert(qr_alt_decoder_feed(&d,rep,8,now+=3,text)==QR_ALT_NONE);
    }
    uint8_t release[8]={0}; assert(qr_alt_decoder_feed(&d,release,8,now+=3,text)==QR_ALT_NONE);
   }
   uint8_t enter[8]={0,0,0x28};
   assert(qr_alt_decoder_feed(&d,enter,8,now+=3,text)==QR_ALT_TEXT);
   assert(strcmp(text,wanted)==0);
   r.seq=emitted++; r.kind=12; r.length=35; memcpy(r.data,text,35);
   assert(probe_stream_push(&q,&r));
   assert(qr_alt_decoder_feed(&d,enter,8,now+=3,text)==QR_ALT_NONE);
   enter[2]=0; assert(qr_alt_decoder_feed(&d,enter,8,now+=3,text)==QR_ALT_NONE);
   assert(probe_stream_pop(&q,&out) && out.seq==scan && memcmp(out.data,wanted,35)==0);
  }
  assert(emitted==200 && q.count==0 && q.dropped==0);
 } else return 2;
 return 0;
}
'''

class NativeStreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tcc=ROOT/'tools/usb_submcu/host-test-tcc/tcc/tcc.exe'
        compiler=str(tcc) if os.name=='nt' and tcc.exists() else shutil.which('cc')
        if not compiler: raise unittest.SkipTest('Native compiler required')
        cls.temp=tempfile.TemporaryDirectory(prefix='qr_stream_')
        p=Path(cls.temp.name); (p/'main.c').write_text(HARNESS,encoding='ascii')
        cls.exe=p/('check.exe' if os.name=='nt' else 'check')
        src=ROOT/'firmware/usb_submcu_host_probe'
        result=subprocess.run([compiler,'-I',str(src),str(p/'main.c'),str(src/'probe_stream.c'),str(src/'qr_alt_decoder.c'),'-o',str(cls.exe)],capture_output=True,text=True)
        if result.returncode:
            cls.temp.cleanup()
            raise RuntimeError(result.stdout+result.stderr)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def check(self,mode): subprocess.run([str(self.exe),str(mode)],check=True,capture_output=True,timeout=20)
    def test_wrap_preserves_ten_thousand_records(self): self.check(1)
    def test_full_does_not_overwrite_and_recovers(self): self.check(2)
    def test_empty_does_not_publish_stale_record(self): self.check(3)
    def test_two_hundred_actual_c_decodes_through_fifo(self): self.check(4)
