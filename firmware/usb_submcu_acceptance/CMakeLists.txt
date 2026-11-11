cmake_minimum_required(VERSION 3.13)
set(PICO_BOARD_HEADER_DIRS "${CMAKE_CURRENT_LIST_DIR}/boards")
set(PICO_BOARD waveshare_rp2350_usb_c_acceptance CACHE STRING "Acceptance board")
set(PICO_PLATFORM rp2350-arm-s CACHE STRING "ARM secure RP2350")
if(NOT DEFINED PICO_SDK_PATH)
    message(FATAL_ERROR "Set PICO_SDK_PATH to the pinned SDK 2.2.0")
endif()
include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)
project(usb_submcu_acceptance C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
if(NOT PICO_SDK_VERSION_STRING STREQUAL "2.2.0")
    message(FATAL_ERROR "This development artifact requires Pico SDK 2.2.0")
endif()
add_executable(usb_submcu_acceptance main.cpp)
file(SHA256 "${CMAKE_CURRENT_LIST_DIR}/main.cpp" SOURCE_HASH)
string(SUBSTRING "${SOURCE_HASH}" 0 16 SOURCE_ID)
target_compile_definitions(usb_submcu_acceptance PRIVATE
    ACCEPTANCE_BUILD_ID="${SOURCE_ID}"
    PICO_STDIO_USB_DEFAULT_CRLF=0
    PICO_STDIO_USB_STDOUT_TIMEOUT_US=100000
    PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=0
    PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE=0
    PICO_USB_DEVICE_MANUFACTURER="NF55G_Development"
    PICO_USB_DEVICE_PRODUCT="USB_SubMCU_Acceptance"
)
target_compile_options(usb_submcu_acceptance PRIVATE -Wall -Wextra -Werror)
target_link_libraries(usb_submcu_acceptance pico_stdlib pico_unique_id)
pico_enable_stdio_usb(usb_submcu_acceptance 1)
pico_enable_stdio_uart(usb_submcu_acceptance 0)
pico_set_program_name(usb_submcu_acceptance "usb_submcu_acceptance")
pico_set_program_version(usb_submcu_acceptance "dev-20261111.1")
pico_add_extra_outputs(usb_submcu_acceptance)
