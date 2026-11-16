// 実機で得た1つのHID形式を35文字へ復元する診断専用モジュール。
// 完成までは公開せず、異常後はEnter境界まで捨てて断片の連結を防ぐ。
#include "qr_alt_decoder.h"
#include <string.h>

static const uint8_t descriptor_expected[] = {
 0x05,0x01,0x09,0x06,0xa1,0x01,0x05,0x07,0x19,0xe0,0x29,0xe7,
 0x15,0x00,0x25,0x01,0x75,0x01,0x95,0x08,0x81,0x02,0x95,0x01,
 0x75,0x08,0x81,0x03,0x95,0x05,0x75,0x01,0x05,0x08,0x19,0x01,
 0x29,0x05,0x91,0x02,0x95,0x01,0x75,0x03,0x91,0x03,0x95,0x06,
 0x75,0x08,0x15,0x00,0x25,0xff,0x05,0x07,0x19,0x00,0x29,0xff,
 0x81,0x00,0xc0
};

bool qr_alt_profile_supported(uint16_t vid, uint16_t pid,
                             const uint8_t *descriptor, size_t size) {
 return vid==0xe851 && pid==0x1001 && descriptor &&
        size==sizeof(descriptor_expected) &&
        memcmp(descriptor,descriptor_expected,size)==0;
}

void qr_alt_decoder_init(qr_alt_decoder_t *s) { memset(s,0,sizeof(*s)); }

static void clear_scan(qr_alt_decoder_t *s) {
 memset(s->text,0,sizeof(s->text));
 s->length=0; s->digits=0; s->value=0; s->active=false;
}

static qr_alt_result_t fail(qr_alt_decoder_t *s, qr_alt_error_t error) {
 clear_scan(s); s->discarding=true; s->error=error;
 return QR_ALT_ERROR;
}

qr_alt_result_t qr_alt_decoder_poll(qr_alt_decoder_t *s, uint32_t now_ms) {
 if(s->active && (uint32_t)(now_ms-s->last_ms)>QR_ALT_IDLE_TIMEOUT_MS)
  return fail(s,QR_ALT_TIMEOUT);
 return QR_ALT_NONE;
}

static bool allowed(uint32_t value) {
 return (value>='A' && value<='Z') || (value>='a' && value<='z') ||
        (value>='0' && value<='9') || value=='-';
}

qr_alt_result_t qr_alt_decoder_feed(qr_alt_decoder_t *s,
 const uint8_t *report, size_t size, uint32_t now_ms, char output[36]) {
 if(size!=8 || !report) return fail(s,QR_ALT_REPORT_SIZE);
 if(report[1]) return fail(s,QR_ALT_RESERVED);
 uint8_t modifier=report[0], key=0;
 unsigned keys=0;
 for(unsigned i=2;i<8;i++) if(report[i]) { key=report[i]; keys++; }
 if(keys>1) return fail(s,QR_ALT_KEY_COUNT);
 if(modifier!=0 && modifier!=4) return fail(s,QR_ALT_MODIFIER);
 bool changed=modifier!=s->previous_modifier || key!=s->previous_key;
 bool pressed=key && key!=s->previous_key;
 bool alt_released=s->previous_modifier==4 && modifier==0;
 s->previous_modifier=modifier; s->previous_key=key;

 qr_alt_result_t timeout=qr_alt_decoder_poll(s,now_ms);
 if(s->discarding) {
  // 破損した試行のEnterを消費してから、次の読取を許可する。
  if(modifier==0 && key==0x28 && pressed) {
   clear_scan(s); s->discarding=false;
  }
  return timeout;
 }
 if(!changed) return QR_ALT_NONE; // 同じ押下報告を文字の再入力にしない。
 if(s->active || modifier==4) { s->active=true; s->last_ms=now_ms; }

 if(alt_released) {
  if(s->digits!=5) return fail(s,QR_ALT_DIGITS);
  if(!allowed(s->value)) return fail(s,QR_ALT_CHARACTER);
  if(s->length>=QR_ALT_TEXT_LENGTH) return fail(s,QR_ALT_LENGTH);
  s->text[s->length++]=(char)s->value;
  s->text[s->length]='\0'; s->digits=0; s->value=0;
 }
 if(modifier==4 && pressed) {
  uint8_t digit;
  if(key==0x62) digit=0;
  else if(key>=0x59 && key<=0x61) digit=(uint8_t)(key-0x58);
  else return fail(s,QR_ALT_KEY);
  if(s->digits>=5) return fail(s,QR_ALT_DIGITS);
  s->value=s->value*10+digit; s->digits++;
 } else if(modifier==0 && pressed) {
  if(key!=0x28) return fail(s,QR_ALT_KEY);
  if(s->length!=QR_ALT_TEXT_LENGTH || s->digits) {
   clear_scan(s); s->error=QR_ALT_LENGTH;
   return QR_ALT_ERROR; // Enterで境界が確定したので次試行まで捨てる必要はない。
  }
  memcpy(output,s->text,QR_ALT_TEXT_LENGTH+1);
  clear_scan(s); s->error=QR_ALT_OK;
  return QR_ALT_TEXT;
 }
 return QR_ALT_NONE;
}
