// 診断用の受付ID。旧HID読取のEnter・キー解放を待ち、以後のQRを1件だけ公開する。
#include "qr_arm_gate.h"
#include <string.h>

void qr_arm_gate_cancel(qr_arm_gate_t *gate) {
 gate->pending=false;
 gate->armed=false;
}

static bool valid_input(const qr_arm_gate_t *gate) {
 if(gate->length!=sizeof(gate->input) || gate->input[0]!='A') return false;
 for(unsigned i=1;i<sizeof(gate->input);i++) {
  char c=gate->input[i];
  if(!((c>='0' && c<='9') || (c>='A' && c<='F'))) return false;
 }
 return true;
}

void qr_arm_gate_input(qr_arm_gate_t *gate, uint8_t byte, uint32_t now) {
 if(byte!='\n') {
  if(gate->length<sizeof(gate->input)) gate->input[gate->length++]=(char)byte;
  else gate->length=sizeof(gate->input)+1;
  return;
 }
 if(valid_input(gate) && (!gate->have_id || memcmp(gate->id,gate->input+1,QR_ARM_ID_SIZE))) {
  memcpy(gate->id,gate->input+1,QR_ARM_ID_SIZE);
  gate->have_id=true;
  gate->requested_ms=now;
  gate->armed=false;
  gate->drained=false;
  gate->pending=true;
 }
 gate->length=0;
}

bool qr_arm_gate_ack(qr_arm_gate_t *gate, const qr_alt_decoder_t *decoder) {
 if(!gate->pending || decoder->active || decoder->discarding ||
    decoder->previous_key || decoder->previous_modifier) return false;
 gate->pending=false;
 gate->armed=true;
 return true;
}

bool qr_arm_gate_take(qr_arm_gate_t *gate) {
 bool armed=gate->armed;
 if(gate->pending) gate->drained=true;
 gate->armed=false;
 return armed;
}

void qr_arm_gate_expire(qr_arm_gate_t *gate, uint32_t now) {
 if((uint32_t)(now-gate->requested_ms)>=65000u) qr_arm_gate_cancel(gate);
}
