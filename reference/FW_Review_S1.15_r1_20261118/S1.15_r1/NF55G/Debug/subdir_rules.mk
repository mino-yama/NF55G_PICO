################################################################################
# Automatically-generated file. Do not edit!
################################################################################

SHELL = cmd.exe

# Each subdirectory must supply rules for building sources it contributes
build-951426209: ../NF55G.syscfg
	@echo 'Building file: "$<"'
	@echo 'Invoking: SysConfig'
	"C:/ti/ccs1281/ccs/utils/sysconfig_1.21.0/sysconfig_cli.bat" --script "C:/Users/k_okui/work/3_other/10_NF/NF55/4_firm/BASE_CS/S1.15_eval/NF55G/NF55G.syscfg" -o "syscfg" -s "C:/ti/mspm0_sdk_2_04_00_06/.metadata/product.json" --compiler ticlang
	@echo 'Finished building: "$<"'
	@echo ' '

syscfg/device.opt: build-951426209 ../NF55G.syscfg
syscfg/device.cmd.genlibs: build-951426209
syscfg/ti_msp_dl_config.c: build-951426209
syscfg/ti_msp_dl_config.h: build-951426209
syscfg/peripheralPinAssignments.txt: build-951426209
syscfg/resourceUsageReport.csv: build-951426209
syscfg/Event.dot: build-951426209
syscfg: build-951426209

syscfg/%.o: ./syscfg/%.c $(GEN_OPTS) | $(GEN_FILES) $(GEN_MISC_FILES)
	@echo 'Building file: "$<"'
	@echo 'Invoking: Arm Compiler'
	"C:/ti/ccs1281/ccs/tools/compiler/ti-cgt-armllvm_3.2.2.LTS/bin/tiarmclang.exe" -c @"syscfg/device.opt"  -march=thumbv6m -mcpu=cortex-m0plus -mfloat-abi=soft -mlittle-endian -mthumb -O1 -I"C:/Users/k_okui/work/3_other/10_NF/NF55/4_firm/BASE_CS/S1.15_eval/NF55G" -I"C:/Users/k_okui/work/3_other/10_NF/NF55/4_firm/BASE_CS/S1.15_eval/NF55G/Debug" -I"C:/ti/mspm0_sdk_2_04_00_06/source/third_party/CMSIS/Core/Include" -I"C:/ti/mspm0_sdk_2_04_00_06/source" -gdwarf-3 -MMD -MP -MF"syscfg/$(basename $(<F)).d_raw" -MT"$(@)" -I"C:/Users/k_okui/work/3_other/10_NF/NF55/4_firm/BASE_CS/S1.15_eval/NF55G/Debug/syscfg"  $(GEN_OPTS__FLAG) -o"$@" "$<"
	@echo 'Finished building: "$<"'
	@echo ' '


