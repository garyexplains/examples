#!/bin/bash
vcgencmd measure_temp
vcgencmd measure_volts core
echo -n "cpu0="
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
echo -n "cpu1="
cat /sys/devices/system/cpu/cpu1/cpufreq/scaling_cur_freq
echo -n "cpu2="
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_cur_freq
echo -n "cpu3="
cat /sys/devices/system/cpu/cpu3/cpufreq/scaling_cur_freq

# 01110000000000000010
#  ||||            ||||_ Under-voltage detected
#  ||||            |||_ Arm frequency capped
#  ||||            ||_ Currently throttled
#  ||||            |_ Soft temperature limit active
#  ||||_ Under-voltage has occurred since last reboot
#  |||_ Arm frequency capped has occurred
#  ||_ Throttling has occurred
#  |_ Soft temperature limit has occurred

THROTTLED_OUTPUT=$(vcgencmd get_throttled)
hex_value=$(echo $THROTTLED_OUTPUT | awk -F'=' '{print $2}')
decimal_number=$((hex_value))
echo -n "throttled="
echo "obase=2;$decimal_number" | bc
echo "Current issues:"
issues=0
if (( (decimal_number & (1<<0)) != 0 )); then
        echo  "+ under-voltage"
        let issues++
fi
if (( (decimal_number & (1<<1)) != 0 )); then
        echo  "+ Arm frequency capped"
        let issues++
fi
if (( (decimal_number & (1<<2)) != 0 )); then
        echo  "+ Currently throttled"
        let issues++
fi
if (( (decimal_number & (1<<3)) != 0 )); then
        echo  "+ Soft temperature limit active"
        let issues++
fi
if (( issues==0 )); then
        echo "- No current issues"
fi
echo "Previously detected issues:"
if (( (decimal_number & (1<<16)) != 0 )); then
        echo  "~ under-voltage"
fi
if (( (decimal_number & (1<<17)) != 0 )); then
        echo  "~ Arm frequency capped"
fi
if (( (decimal_number & (1<<18)) != 0 )); then
        echo  "~ Throttled"
fi
if (( (decimal_number & (1<<19)) != 0 )); then
        echo  "~ Soft temperature limit"
fi
