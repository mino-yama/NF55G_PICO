cmake_minimum_required(VERSION 3.13)

set(PICO_BOARD_HEADER_DIRS "${CMAKE_CURRENT_LIST_DIR}/boards")
set(PICO_BOARD waveshare_rp2350_usb_a_host_eval CACHE STRING "External instrument Host board")
set(PICO_PLATFORM rp2350-arm-s CACHE STRING "RP2350 secure ARM platform")
set(PICO_PIO_USB_PATH "${CMAKE_CURRENT_LIST_DIR}/../usb_submcu_host_probe/vendor/pico-pio-usb")
include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(usb_submcu_external_meter_host C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

pico_sdk_init()

if(NOT PICO_SDK_VERSION_STRING STREQUAL "2.2.0")
    message(FATAL_ERROR "Pinned Pico SDK 2.2.0 required")
endif()

add_executable(usb_submcu_external_meter_host
    main.c
    newlib_malloc_lock.c
)

target_include_directories(usb_submcu_external_meter_host PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_compile_definitions(usb_submcu_external_meter_host PRIVATE
    CFG_TUH_RPI_PIO_USB=1
    HOST_FW_VERSION="meter-host-diag-20261119.1"
)

target_compile_options(usb_submcu_external_meter_host PRIVATE
    -Wall
    -Wextra
    -Werror
)

target_link_libraries(usb_submcu_external_meter_host PRIVATE
    pico_stdlib
    pico_unique_id
    hardware_clocks
    hardware_uart
    tinyusb_host
    tinyusb_pico_pio_usb
)

pico_enable_stdio_usb(usb_submcu_external_meter_host 0)
pico_enable_stdio_uart(usb_submcu_external_meter_host 0)
pico_set_program_name(usb_submcu_external_meter_host "usb_submcu_external_meter_host")
pico_set_program_version(usb_submcu_external_meter_host "meter-host-diag-20261119.1")
pico_add_extra_outputs(usb_submcu_external_meter_host)

add_executable(usb_submcu_external_meter_voltage_test
    main.c
    newlib_malloc_lock.c
)

target_include_directories(usb_submcu_external_meter_voltage_test PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_compile_definitions(usb_submcu_external_meter_voltage_test PRIVATE
    CFG_TUH_RPI_PIO_USB=1
    HOST_VOLTAGE_TEST=1
    HOST_FW_VERSION="meter-host-voltage-test-20261120.4"
)

target_compile_options(usb_submcu_external_meter_voltage_test PRIVATE
    -Wall
    -Wextra
    -Werror
)

target_link_libraries(usb_submcu_external_meter_voltage_test PRIVATE
    pico_stdlib
    pico_unique_id
    hardware_clocks
    hardware_uart
    tinyusb_host
    tinyusb_pico_pio_usb
)

pico_enable_stdio_usb(usb_submcu_external_meter_voltage_test 0)
pico_enable_stdio_uart(usb_submcu_external_meter_voltage_test 0)
pico_set_program_name(usb_submcu_external_meter_voltage_test "usb_submcu_external_meter_voltage_test")
pico_set_program_version(usb_submcu_external_meter_voltage_test "meter-host-voltage-test-20261120.4")
pico_add_extra_outputs(usb_submcu_external_meter_voltage_test)