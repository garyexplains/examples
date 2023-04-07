"""Driver for AHT2x sensors (humidity and temperature):
    Models: AHT20 and AHT21
    Adresse i2c: 56 (0x3b)
    Official website of the manufacturer: http://www.aosong.com
"""

import time
from micropython import const

__author__ = "Jonathan Fromentin"
__credits__ = ["Jonathan Fromentin"]
__license__ = "CeCILL version 2.1"
__version__ = "1.1.0"
__maintainer__ = "Jonathan Fromentin"


AHT_I2C_ADDR = const(0x38)  # Default I2C address
AHT_STATUS_BUSY = const(0x01)  # Status bit for busy
AHT_STATUS_CALIBRATED = const(0x10)  # status bit for calibrated
AHT_CMD_INIT = const(0xBE)  # command for initialization
AHT_CMD_TRIGGER = const(0xAC)  # command for trigger measurement
AHT_CMD_RESET = const(0xBA)  # command for soft reset
AHT_CRC_POLYNOMIAL = const(0x31)  # Polynomial representation
AHT_CRC_MSB = const(0x80)  # Most significant bit
AHT_CRC_INIT = const(0xFF)  # Initial value of CRC


class AHT2x:
    """Class based on AHT20 and AHT21 documentation."""

    def __init__(self, i2c, address=AHT_I2C_ADDR, crc=False):
        """Parameters:
        i2c: instance of machine.I2C
        address: i2c address of sensor
        crc: Boolean for CRC control. True to active the CRC control."""
        time.sleep(0.04)  # Wait  40ms  after  power-on.
        self.i2c = i2c
        self.address = address
        self.active_crc = crc
        self._buf = bytearray(6 + crc)  # Request the CRC byte only if necessary
        self._values = {"hum": None, "temp": None}
        self._reload = {"hum": True, "temp": True}
        while not self.is_calibrated:
            self._calibrate()

    @property
    def is_busy(self):
        """The sensor is busy until the measurement is complete."""
        return bool(self._status() & AHT_STATUS_BUSY)

    @property
    def is_calibrated(self):
        """The activation of the calibration must be done before any
        measurement. If not, do a soft reset."""
        return bool(self._status() & AHT_STATUS_CALIBRATED)

    def _status(self):
        """The status byte initially returned from the sensor.
        Bit     Definition  Description
        [0:2]   Remained    Remained
        [3]     CAL Enable  0:Uncalibrated,1:Calibrated
        [4]     Remained    Remained
        [5:6]   Remained    Remained
        [7]     Busy        0:Free in dormant state, 1:Busy in measurement"""
        self.i2c.readfrom_into(self.address, self._buf)

        if not self.active_crc or (self._crc8() == self._buf[6]):
            return self._buf[0]
        return AHT_STATUS_BUSY  # Return the status busy and uncalibrated

    @property
    def humidity(self):
        """The measured relative humidity in percent."""
        if self._reload["hum"]:
            self._measure()
            self._reload["temp"] = False
        else:
            self._reload["hum"] = True

        return self._values["hum"]

    @property
    def temperature(self):
        """The measured temperature in degrees Celsius."""
        if self._reload["temp"]:
            self._measure()
            self._reload["hum"] = False
        else:
            self._reload["temp"] = True

        return self._values["temp"]

    def reset(self):
        """The soft reset command is used to restart the sensor system without
        turning the power off and on again. After receiving this command, the
        sensor system begins to re-initialize and restore the default setting
        state"""
        self._buf[0] = AHT_CMD_RESET
        self.i2c.writeto(self.address, self._buf[:1])
        time.sleep(0.02)  # The time required for reset does not exceed 20 ms

        # The soft reset is badly documented. It is therefore possible that it
        # is necessary to calibrate the sensor after a soft reset.
        while not self.is_calibrated:
            self._calibrate()

    def _calibrate(self):
        """Internal function to send initialization command.
        Note: The  calibration  status  check  in  the  first  step
            only  needs  to  be  checked  at  power-on.  No  operation is
            required during the normal acquisition process."""
        self._buf[0] = AHT_CMD_INIT
        self._buf[1] = 0x08
        self._buf[2] = 0x00
        self.i2c.writeto(self.address, self._buf[:3])
        time.sleep(0.01)  # Wait initialization process

    def _crc8(self):
        """Internal function to calcule the CRC-8-Dallas/Maxim of current
        message. The initial value of CRC is 0xFF, and the CRC8 check
        polynomial is: CRC [7:0] = 1+X^4 +X^5 +X^8"""
        crc = bytearray(1)
        crc[0] = AHT_CRC_INIT
        for byte in self._buf[:6]:
            crc[0] ^= byte
            for _ in range(8):
                if crc[0] & AHT_CRC_MSB:
                    crc[0] = (crc[0] << 1) ^ AHT_CRC_POLYNOMIAL
                else:
                    crc[0] = crc[0] << 1

        return crc[0]

    def _measure(self):
        """Internal function for triggering the AHT to read temp/humidity"""
        self._buf[0] = AHT_CMD_TRIGGER
        self._buf[1] = 0x33
        self._buf[2] = 0x00
        self.i2c.writeto(self.address, self._buf[:3])
        time.sleep(0.08)  # Wait 80ms for the measurement to be completed.
        while self.is_busy:
            time.sleep(0.01)
        self.i2c.readfrom_into(self.address, self._buf)

        if not self.active_crc or (self._crc8() == self._buf[6]):
            self._values["hum"] = (
                (self._buf[1] << 12) | (self._buf[2] << 4) | (self._buf[3] >> 4)
            )
            self._values["hum"] = (self._values["hum"] * 100) / 0x100000
            self._values["temp"] = (
                ((self._buf[3] & 0xF) << 16) | (self._buf[4] << 8) | self._buf[5]
            )
            self._values["temp"] = ((self._values["temp"] * 200.0) / 0x100000) - 50
        else:
            self._values["hum"] = 0
            self._values["temp"] = 0
