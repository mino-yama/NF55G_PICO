/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2019 Ha Thach (tinyusb.org)
 *                    sekigon-gonnoc
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

// This example runs both host and device concurrently. The USB host receive
// reports from HID device and print it out over USB Device CDC interface.
// For TinyUSB roothub port0 is native usb controller, roothub port1 is
// pico-pio-usb.

// updated for RP2350-USB-A Host HID to UART

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "hardware/clocks.h"
#include "hardware/uart.h"
#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/bootrom.h"

#include "pio_usb.h"
#include "tusb.h"

#include "hardware/pio.h"
#include "ws2812.pio.h"

#define _AZERTY_

#ifdef _AZERTY_

/*
static uint8_t const keycode2ascii_azerty[][2] = {
    // [Keycode]       = { Normal, Shift }
    [HID_KEY_A]        = { 'q', 'Q' }, // Position du A sur AZERTY = Q sur QWERTY
    [HID_KEY_Q]        = { 'a', 'A' }, // Et inversement
    [HID_KEY_W]        = { 'z', 'Z' },
    [HID_KEY_Z]        = { 'w', 'W' },
    [HID_KEY_M]        = { ',', '?' },
    [HID_KEY_COMMA]    = { ';', '.' },
    [HID_KEY_SEMICOLON]= { 'm', 'M' },

};
*/

/*
static uint8_t const transcode_ascii_qwerty_azerty[][3] = {
	{HID_KEY_A, 'q', 'Q' }, 
	{HID_KEY_Q, 'a', 'A' },
	{HID_KEY_W, 'z', 'Z' },
	{HID_KEY_Z, 'w', 'W' },
	{HID_KEY_M, ',', '?' },
	{HID_KEY_COMMA, ';', '.' },
	{HID_KEY_SEMICOLON, 'm', 'M' },	
    // ... à compléter pour les chiffres et symboles ...	
};
*/

static uint8_t const transcode_ascii_qwerty_azerty[][3] = {
//  { HID_KEYCODE, 			Normal, Shift }

	// Lettres qui permutent
    { HID_KEY_A,            'q', 'Q' },
    { HID_KEY_Q,            'a', 'A' },
    { HID_KEY_W,            'z', 'Z' },
    { HID_KEY_Z,            'w', 'W' },
    { HID_KEY_M,            ',', '?' },

    // Chiffres (Inversion Normal/Shift par rapport au US)
    { HID_KEY_1,            '&', '1' },
    { HID_KEY_2,            0xE9, '2' }, // é
    { HID_KEY_3,            '\"', '3' },
    { HID_KEY_4,            '\'', '4' },
    { HID_KEY_5,            '(', '5' },
    { HID_KEY_6,            '-', '6' },
    { HID_KEY_7,            0xE8, '7' }, // è
    { HID_KEY_8,            '_', '8' },
    { HID_KEY_9,            0xE7, '9' }, // ç
    { HID_KEY_0,            0xE0, '0' }, // à

    // Ponctuation spécifique
    { HID_KEY_MINUS,        ')', 0xF8 }, // ) et °
    { HID_KEY_SEMICOLON,    'm', 'M' },
    { HID_KEY_APOSTROPHE,   '%', 0xF9 }, // ù
    { HID_KEY_COMMA,        ';', '.' },
    { HID_KEY_PERIOD,       ':', '/' },
    { HID_KEY_SLASH,        '!', 0x00 },
    { HID_KEY_GRAVE,        0xB2, 0x00 }, // ²
    { HID_KEY_BRACKET_LEFT, '^', 0x00 },
    { HID_KEY_BRACKET_RIGHT, '$', '*' },
	
	//{ HID_KEY_BACKSLASH,	'%', 
};

// ch = transcode_azerty(ch, keycode, (shift_toggle ^ is_shift));
	
char transcode_azerty(char ch, uint8_t keycode, bool shift) {
	uint8_t len = sizeof(transcode_ascii_qwerty_azerty) / (3 * sizeof(uint8_t));
	for (uint8_t i=0;i<len;i++) {
		if (transcode_ascii_qwerty_azerty[i][0] == keycode) {
			return transcode_ascii_qwerty_azerty[i][1+shift];
		}
	}	
	return ch;
}
#endif /* _AZERTY_ */

//--------------------------------------------------------------------+
// MACRO CONSTANT TYPEDEF PROTYPES
//--------------------------------------------------------------------+
#define UART_ID uart0
#define BAUD_RATE 115200

// Broches par défaut pour UART0 sur RP2350
#define UART_TX_PIN 0
#define UART_RX_PIN 1

static uint8_t const keycode2ascii[128][2] =  { HID_KEYCODE_TO_ASCII };

static volatile uint8_t keyboard_led = 0;
static volatile uint8_t old_keyboard_led = 0;

static volatile uint16_t keyboard_dev_addr = 0x0000;
static volatile uint16_t keyboard_instance = 0x0000;
 
void setup_uart_for_fpga() {
    // Initialisation de l'UART à 115200 bauds
    uart_init(UART_ID, BAUD_RATE);

    // Configurer les fonctions GPIO pour l'UART
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    // Optionnel : Désactiver le contrôle de flux matériel (CTS/RTS)
    uart_set_hw_flow(UART_ID, false, false);
}

void send_frame_to_fpga(uint8_t *tx_buffer, uint8_t len) {
	uint16_t chksum = 0;
	uart_putc(UART_ID, 0xFF);									// Preamble	
	for (int i=0;i<len;i++) {
		uart_putc(UART_ID, tx_buffer[i]);
		chksum += tx_buffer[i];
	}
	uart_putc(UART_ID, (uint8_t)(chksum>>8) ^ ~(chksum>>0));	// crc H
	uart_putc(UART_ID, (uint8_t)(chksum>>0));					// crc L
}




void send_short_frame_to_fpga(uint8_t status) {
	uint8_t len = 1;
	uint8_t tx_buffer[2+len];
	uint8_t ix = 0;											
	tx_buffer[ix++] = 0x50;
	tx_buffer[ix++] = len;										// Length	
	tx_buffer[ix++] = status;									// status
	
	send_frame_to_fpga(tx_buffer, ix);
}

void send_key_frame_to_fpga(hid_keyboard_report_t const *report, char last_key_ascii) {
	//uint8_t report_size = sizeof(hid_keyboard_report_t);

	uint8_t len = 2+6;
	uint8_t tx_buffer[2+len];
	uint8_t ix = 0;
	tx_buffer[ix++] = 0x60 | (keyboard_led & 0x07);				// Keyboard Id & keyboard_led
	tx_buffer[ix++] = len;										// Length
	
	tx_buffer[ix++] = (uint8_t)last_key_ascii;					// ascii decoded key
	tx_buffer[ix++] = report->modifier;							// report modifier
	for (int i=0;i<6;i++) {		
		tx_buffer[ix++] = report->keycode[i];					// 6 x keycode;		
	}
	
	send_frame_to_fpga(tx_buffer, ix);
}


void set_keyboard_leds(uint8_t leds) {
	if (keyboard_dev_addr>0) {	
		tuh_hid_set_report(keyboard_dev_addr, keyboard_instance, 0, HID_REPORT_TYPE_OUTPUT, &leds, sizeof(leds));
	}
}





#define W2812_STATE_OFF					0x000000
#define W2812_STATE_KEYBOARD_OFF		0x400000
#define W2812_STATE_KEYBOARD_READY		0x001000
#define W2812_STATE_KEY_PRESSED			0x004000


typedef enum {State_Reset=0, State_Off, State_Ready, State_KeyPressed} w2812_state_t;

static volatile w2812_state_t current_state = State_Reset;
static volatile bool any_key_pressed = false;
//static volatile bool keyboard_connected = false;
	
static PIO W2812_pio = pio2;	// only on pico2

void put_pixel(uint32_t pixel_rgb) {
    pio_sm_put_blocking(W2812_pio, 0, pixel_rgb << 8u);
}

void setup_w2812(void) {    	
    int8_t sm = 0;
    uint32_t offset = pio_add_program(W2812_pio, &ws2812_program);
	ws2812_program_init(W2812_pio, sm, offset, 16, 800000, true);	
}   
	

void W2812_state_fsm(void) {
    //static w2812_state_t last_rendered_state = State_Reset;

    switch (current_state) {
        case State_Off:		
            put_pixel(W2812_STATE_KEYBOARD_OFF); // ROUGE
            break;

        case State_Ready:
        case State_KeyPressed:
            // Si on est dans un état "connecté", on check les touches
            if (any_key_pressed) {
                current_state = State_KeyPressed;
                put_pixel(W2812_STATE_KEY_PRESSED);     // VERT BRILLANT
            } else {
                current_state = State_Ready;
                put_pixel(W2812_STATE_KEYBOARD_READY); // VERT SOMBRE
            }
            break;

        default:
            put_pixel(W2812_STATE_OFF);
			current_state = State_Off;
            break;
    }
}


struct repeating_timer timer;

bool led_update_callback(struct repeating_timer *t) {
	(void)t;
	
    W2812_state_fsm();
    return true; // Continuer le timer
}

/*------------- MAIN -------------*/


// core1: handle host events
void core1_main() {
	sleep_ms(10);

	// Use tuh_configure() to pass pio configuration to the host stack
	// Note: tuh_configure() must be called before
	pio_usb_configuration_t pio_cfg = PIO_USB_DEFAULT_CONFIG;

	pio_cfg.pin_dp = 12;					// DP = 		GPIO12
	pio_cfg.pinout = PIO_USB_PINOUT_DPDM;	// DM = DP+1 =	GPIO13


	tuh_configure(1, TUH_CFGID_RPI_PIO_USB_CONFIGURATION, &pio_cfg);

	// To run USB SOF interrupt in core1, init host stack for pio_usb (roothub
	// port1) on core1
	tuh_init(1);
	
	setup_uart_for_fpga();
	
	setup_w2812();
	
	add_repeating_timer_ms(20, led_update_callback, NULL, &timer);
	
	while (true) {  
		
		if (keyboard_led != old_keyboard_led) {
			old_keyboard_led = keyboard_led;		
			set_keyboard_leds(keyboard_led);			
		}

		tuh_task(); // tinyusb host task			
	}
}

// core0: handle device events
int main(void) {
	// default 125MHz is not appropreate. Sysclock should be multiple of 12MHz.
	set_sys_clock_khz(120000, true);

	sleep_ms(10);

	printf("Start Core1...");

	multicore_reset_core1();
	// all USB task run in core1
	multicore_launch_core1(core1_main);

	// init device stack on native usb (roothub port0)
	tud_init(0);

	while (true) {
		tud_task(); // tinyusb device task
		tud_cdc_write_flush();
	}

	return 0;
}

//--------------------------------------------------------------------+
// Device CDC
//--------------------------------------------------------------------+

// Invoked when CDC interface received data from host
void tud_cdc_rx_cb(uint8_t itf) {
	(void) itf;

	char buf[64];
	uint32_t count = tud_cdc_read(buf, sizeof(buf));

	// TODO control LED on keyboard of host stack
	(void) count;
}

//--------------------------------------------------------------------+
// Host HID
//--------------------------------------------------------------------+

// Invoked when device with hid interface is mounted
// Report descriptor is also available for use. tuh_hid_parse_report_descriptor()
// can be used to parse common/simple enough descriptor.
// Note: if report descriptor length > CFG_TUH_ENUMERATION_BUFSIZE, it will be skipped
// therefore report_desc = NULL, desc_len = 0
void tuh_hid_mount_cb(uint8_t dev_addr, uint8_t instance, uint8_t const* desc_report, uint16_t desc_len) {
	(void)desc_report;
	(void)desc_len;

	// Interface protocol (hid_interface_protocol_enum_t)
	const char* protocol_str[] = { "None", "Keyboard", "Mouse" };
	uint8_t const itf_protocol = tuh_hid_interface_protocol(dev_addr, instance);

	uint16_t vid, pid;
	tuh_vid_pid_get(dev_addr, &vid, &pid);

	char tempbuf[256];
	int count = sprintf(tempbuf, "[%04x:%04x][%u] HID Interface%u, Protocol = %s\r\n", vid, pid, dev_addr, instance, protocol_str[itf_protocol]);

	tud_cdc_write(tempbuf, count);
	tud_cdc_write_flush();

	// Receive report from boot keyboard & mouse only
	// tuh_hid_report_received_cb() will be invoked when report is available
	switch (itf_protocol) {
		case HID_ITF_PROTOCOL_KEYBOARD : 
			if ( !tuh_hid_receive_report(dev_addr, instance) ) {
				tud_cdc_write_str("Error: cannot request report\r\n");
			}
			keyboard_dev_addr = dev_addr;
			keyboard_instance = instance;
			
			keyboard_led = 0x00;	//KEYBOARD_LED_NUMLOCK;
			old_keyboard_led = 0x00;
			send_short_frame_to_fpga(0x01);
			
			//put_pixel(W2812_STATE_KEYBOARD_READY);
			current_state = State_Ready;
		break;
		
		case HID_ITF_PROTOCOL_MOUSE:
		
			if ( !tuh_hid_receive_report(dev_addr, instance) ) {
				tud_cdc_write_str("Error: cannot request report\r\n");
			}
		break;
	}
}

// Invoked when device with hid interface is un-mounted
void tuh_hid_umount_cb(uint8_t dev_addr, uint8_t instance) {
	char tempbuf[256];
	int count = sprintf(tempbuf, "[%u] HID Interface%u is unmounted\r\n", dev_addr, instance);
	tud_cdc_write(tempbuf, count);
	tud_cdc_write_flush();
	
	if (keyboard_dev_addr == dev_addr) {		
		keyboard_dev_addr = 0x0000;
		send_short_frame_to_fpga(0x00);
	}
	if (keyboard_instance == instance) {		
		keyboard_instance = 0x0000;
	}	
	//put_pixel(W2812_STATE_KEYBOARD_OFF);
	current_state = State_Off;
}

// look up new key in previous keys
static inline bool find_key_in_report(hid_keyboard_report_t const *report, uint8_t keycode) {
	for(uint8_t i=0; i<6; i++) {
		if (report->keycode[i] == keycode)  return true;
	}

	return false;
}

static inline bool is_any_key_pressed(hid_keyboard_report_t const *report) {

	if (report->modifier != 0)
		return true;
	
	for(uint8_t i=0; i<6; i++) {
		if (report->keycode[i] != 0) 
			return true;
	}
	
	return false;	
}

// convert hid keycode to ascii and print via usb device CDC (ignore non-printable)
static void process_kbd_report(uint8_t dev_addr, hid_keyboard_report_t const *report) {
	(void) dev_addr;
	static hid_keyboard_report_t prev_report = { 0, 0, {0} }; // previous report to check key released
	bool flush = false;
	uint8_t last_key_ascii = 0;

	for(uint8_t i=0; i<6; i++) {
		uint8_t keycode = report->keycode[i];
		if ( keycode ) {
			if ( find_key_in_report(&prev_report, keycode) ) {
			// exist in previous report means the current key is holding		
			} else {
				// not existed in previous report means the current key is pressed
				bool const is_shift = report->modifier & (KEYBOARD_MODIFIER_LEFTSHIFT | KEYBOARD_MODIFIER_RIGHTSHIFT);	
				bool shift_toggle = (keyboard_led & KEYBOARD_LED_CAPSLOCK);
				uint8_t ch = keycode2ascii[keycode][(shift_toggle ^ is_shift) ? 1 : 0];
#ifdef _AZERTY_
				ch = transcode_azerty(ch, keycode, (shift_toggle ^ is_shift));
#endif
				if (ch) {
					last_key_ascii = ch;
					if (ch == '\n') tud_cdc_write("\r", 1);
					tud_cdc_write(&ch, 1);
					
					flush = true;
				}				
			}
		}
	// TODO example skips key released
	}

	switch (report->keycode[0]) {
		case HID_KEY_CAPS_LOCK:	// Caps Lock
			keyboard_led ^= KEYBOARD_LED_CAPSLOCK;
		break;
		
		case HID_KEY_NUM_LOCK:	// Numeric Pad
			keyboard_led ^= KEYBOARD_LED_NUMLOCK;
		break;
		
		case HID_KEY_SCROLL_LOCK:	// Scroll Lock
			keyboard_led ^= KEYBOARD_LED_SCROLLLOCK;
		break;
		
		default:
	}
	
	send_key_frame_to_fpga(report, last_key_ascii);
	
	any_key_pressed = is_any_key_pressed(report);
	
	if (flush) {		
		tud_cdc_write_flush();
	}
	prev_report = *report;
}

// send mouse report to usb device CDC
static void process_mouse_report(uint8_t dev_addr, hid_mouse_report_t const * report) {
	//------------- button state  -------------//
	//uint8_t button_changed_mask = report->buttons ^ prev_report.buttons;
	char l = report->buttons & MOUSE_BUTTON_LEFT   ? 'L' : '-';
	char m = report->buttons & MOUSE_BUTTON_MIDDLE ? 'M' : '-';
	char r = report->buttons & MOUSE_BUTTON_RIGHT  ? 'R' : '-';

	char tempbuf[32];
	int count = sprintf(tempbuf, "[%u] %c%c%c %d %d %d\r\n", dev_addr, l, m, r, report->x, report->y, report->wheel);

	tud_cdc_write(tempbuf, count);
	tud_cdc_write_flush();
}



// Invoked when received report from device via interrupt endpoint
void tuh_hid_report_received_cb(uint8_t dev_addr, uint8_t instance, uint8_t const* report, uint16_t len) {
	(void) len;
	uint8_t const itf_protocol = tuh_hid_interface_protocol(dev_addr, instance);

	switch(itf_protocol) {
		case HID_ITF_PROTOCOL_KEYBOARD:
			process_kbd_report(dev_addr, (hid_keyboard_report_t const*) report );
		break;

		case HID_ITF_PROTOCOL_MOUSE:
			process_mouse_report(dev_addr, (hid_mouse_report_t const*) report );
		break;

		default: 
		break;
	}

	// continue to request to receive report
	if ( !tuh_hid_receive_report(dev_addr, instance) ) {
		tud_cdc_write_str("Error: cannot request report\r\n");
	}
}
