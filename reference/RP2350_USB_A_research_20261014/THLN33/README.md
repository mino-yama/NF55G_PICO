# RP2350-USB-A Host-to-FPGA Bridge

This project repurposes the **Waveshare RP2350-USB-A** development board as a USB HID Host gateway. It translates USB keyboard events into a structured UART protocol designed for integration with FPGA-based SoCs, such as the **PicoRV32**.

This implementation leverages the **Pico-PIO-USB** library to provide USB Host capabilities on GPIO pins while maintaining a standard USB Device connection for debugging.

---

## 🛠 Hardware Modification (Mandatory)

The Waveshare RP2350-USB-A board has a design flaw for USB Host applications on the USB-A female port. By default, it is configured as a Device. To enable **Host Mode**, you must perform the following "Hard-Mod":

* **Special thanks to Quentin Santos who for resolving the host-mode connection issue. [Here](https://qsantos.fr/2025/11/21/fixing-the-rp2350-usb-a-not-working-as-usb-host/)'s the link to his blog.**	

1.  **Remove R13**: Remove the 1.5kΩ pull-up resistor on the D+ line.
2.  **Add Pull-downs**: Solder two **15kΩ resistors** between **D+ (GP12) / GND** and **D- (GP13) / GND**.

> **Note**: Without this modification, the USB Host stack will fail to detect any device insertion due to incorrect voltage levels on the data lines.


![Photo](images/RP2350-USB-A-modified.jpg)

---

## 🛠 Software Modification

**Note from [Waveshare](https://www.waveshare.com/wiki/RP2350-USB-A?#Host_hid_to_device_cdc_Demo)**: When compiling this projet, you need to comment the return statement in the SDK\lib\tinyusb\src\portable\raspberrypi\pio_usb\hcd_pio_usb.c file, as follows:
```
bool hcd_edpt_abort_xfer(uint8_t rhport, uint8_t dev_addr, uint8_t ep_addr) {
  uint8_t const pio_rhport = RHPORT_PIO(rhport);
  // return pio_usb_host_endpoint_abort_transfer(pio_rhport, dev_addr, ep_addr);
}        

uint32_t hcd_frame_number(uint8_t rhport) {
  (void) rhport;
  // return pio_usb_host_get_frame_number();
}  

```

---

## 🔌 Pin Mapping (Waveshare Board)

* **USB-A D+**: GPIO 12
* **USB-A D-**: GPIO 13
* **UART TX (to FPGA)**: GPIO 0
* **UART RX (from FPGA)**: GPIO 1
* **WS2812 RGB LED**: GPIO 16 (Driven by PIO2 )
---

## 🚀 Key Features

* **Dual-Core Processing**:
    * **Core 0**: Handles the native USB Device stack (CDC) for PC debugging and terminal output.
    * **Core 1**: Dedicated to the **Pio-USB Host** stack and UART transmission to ensure zero-latency HID processing.
* **Smart Status LED (WS2812)**: Uses a dedicated **Hardware Repeating Timer** (50Hz) and **PIO2** to provide real-time visual feedback:
    * 🔴 **Red**: No keyboard detected.
    * 🟢 **Dim Green**: Keyboard connected & ready.
    * 🌟 **Bright Green**: Key press event detected.      
* **Custom UART Protocol**: Sends structured frames including Preamble, ASCII decoding, raw HID keycodes, LED status, and a 16-bit Checksum.
* **Bidirectional LED Sync**: Supports synchronization of Caps Lock, Num Lock, and Scroll Lock LEDs between the physical keyboard and the FPGA state.
* **Hot-Plug Events**: Sends "Mount/Unmount" status frames (ID `0x50`) to notify the FPGA of hardware changes.

---

## 📡 UART Communication Protocol

The RP2350 communicates with the FPGA via **UART0** at **115200 baud**.

### Data Frame Structure (13 Bytes)

![Capture](images/Capture-1.png)


| Byte | Name | Description |
| :--- | :--- | :--- |
| 0 | **Preamble** | Always `0xFF`. Used for FSM synchronization. |
| 1 | **ID & LEDs** | `0x60` (Keyboard ID) ORed with 3-bit LED status (Bits 0-2). |
| 2 | **Length** | Total data length (usually `0x08`). |
| 3 | **ASCII Key** | Decoded ASCII character (handles Shift/CapsLock logic). |
| 4 | **Modifier** | HID Modifiers (Ctrl, Shift, Alt, GUI). |
| 5-10 | **Keycodes** | Raw 6-Key Rollover HID report data. |
| 11 | **CRC High** | Checksum High: `(sum >> 8) ^ ~(sum >> 0)`. |
| 12 | **CRC Low** | Checksum Low: `(sum >> 0)`. |

---



## 📂 Repository Structure

* `/examples/host_hid_to_fpga`: Optimized source code for the bridge.
* `/images`: Hardware modification photos and Logic Analyzer / Oscilloscope captures.
* `/binary`: Precompiled binary file
* Others: Original Pico-PIO-USB sources code.

## ⚖️ License

This project is released under the **MIT License**. It includes code from the [Pico-PIO-USB](https://github.com/sekigon-gonnoc/Pico-PIO-USB) and [TinyUSB](https://github.com/hathach/tinyusb) projects.
