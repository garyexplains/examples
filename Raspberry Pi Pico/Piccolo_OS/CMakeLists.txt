# Generated Cmake Pico project file

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# initalize pico_sdk from installed location
# (note this can come from environment, CMake cache etc)
set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})

# Pull in Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(piccolo_os_demo C CXX ASM)

# Initialise the Pico SDK
pico_sdk_init()

# Add executable. Default name is the project name, version 0.1

add_executable(piccolo_os_demo piccolo_os_demo.c context_switch.s piccolo_os.c)

pico_set_program_name(piccolo_os_demo "piccolo_os_demo")
pico_set_program_version(piccolo_os_demo "0.1")

pico_enable_stdio_uart(piccolo_os_demo 1)
pico_enable_stdio_usb(piccolo_os_demo 0)

# Add the standard library to the build
target_link_libraries(piccolo_os_demo pico_stdlib)

pico_add_extra_outputs(piccolo_os_demo)

