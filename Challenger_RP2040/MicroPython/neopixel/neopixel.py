# https://github.com/blaz-r/pi_pico_neopixel/blob/main/neopixel.py

import array, time
from machine import Pin
import rp2


# PIO state machine for RGB. Pulls 24 bits (rgb -> 3 * 8bit) automatically
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


# PIO state machine for RGBW. Pulls 32 bits (rgbw -> 4 * 8bit) automatically
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=32)
def sk6812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


# we need this because Micropython can't construct slice objects directly, only by
# way of supporting slice notation.
# So, e.g. slice_maker[1::4] gives a slice(1,None,4) object.
class slice_maker_class:
    def __getitem__(self, slc):
        return slc


slice_maker = slice_maker_class()


# Delay here is the reset time. You need a pause to reset the LED strip back to the initial LED
# however, if you have quite a bit of processing to do before the next time you update the strip
# you could put in delay=0 (or a lower delay)
#
# Class supports different order of individual colors (GRB, RGB, WRGB, GWRB ...). In order to achieve
# this, we need to flip the indexes: in 'RGBW', 'R' is on index 0, but we need to shift it left by 3 * 8bits,
# so in it's inverse, 'WBGR', it has exactly right index. Since micropython doesn't have [::-1] and recursive rev()
# isn't too efficient we simply do that by XORing (operator ^) each index with 3 (0b11) to make this flip.
# When dealing with just 'RGB' (3 letter string), this means same but reduced by 1 after XOR!.
# Example: in 'GRBW' we want final form of 0bGGRRBBWW, meaning G with index 0 needs to be shifted 3 * 8bit ->
# 'G' on index 0: 0b00 ^ 0b11 -> 0b11 (3), just as we wanted.
# Same hold for every other index (and - 1 at the end for 3 letter strings).

class Neopixel:
    # Micropython doesn't implement __slots__, but it's good to have a place
    # to describe the data members...
    # __slots__ = [
    #    'num_leds',   # number of LEDs
    #    'pixels',     # array.array('I') of raw data for LEDs
    #    'mode',       # mode 'RGB' etc
    #    'W_in_mode',  # bool: is 'W' in mode
    #    'sm',         # state machine
    #    'shift',      # shift amount for each component, in a tuple for (R,B,G,W)
    #    'delay',      # delay amount
    #    'brightnessvalue', # brightness scale factor 1..255
    # ]

    def __init__(self, num_leds, state_machine, pin, mode="RGB", delay=0.0001):
        """
        Constructor for library class

        :param num_leds:  number of leds on your led-strip
        :param state_machine: id of PIO state machine used
        :param pin: pin on which data line to led-strip is connected
        :param mode: [default: "RGB"] mode and order of bits representing the color value.
        This can be any order of RGB or RGBW (neopixels are usually GRB)
        :param delay: [default: 0.0001] delay used for latching of leds when sending data
        """
        self.pixels = array.array("I", [0] * num_leds)
        self.mode = mode
        self.W_in_mode = 'W' in mode
        if self.W_in_mode:
            # RGBW uses different PIO state machine configuration
            self.sm = rp2.StateMachine(state_machine, sk6812, freq=8000000, sideset_base=Pin(pin))
            # tuple of values required to shift bit into position (check class desc.)
            self.shift = ((mode.index('R') ^ 3) * 8, (mode.index('G') ^ 3) * 8,
                          (mode.index('B') ^ 3) * 8, (mode.index('W') ^ 3) * 8)
        else:
            self.sm = rp2.StateMachine(state_machine, ws2812, freq=8000000, sideset_base=Pin(pin))
            self.shift = (((mode.index('R') ^ 3) - 1) * 8, ((mode.index('G') ^ 3) - 1) * 8,
                          ((mode.index('B') ^ 3) - 1) * 8, 0)
        self.sm.active(1)
        self.num_leds = num_leds
        self.delay = delay
        self.brightnessvalue = 255

    def brightness(self, brightness=None):
        """
        Set the overall value to adjust brightness when updating leds
        or return class brightnessvalue if brightness is None

        :param brightness: [default: None] Value of brightness on interval 1..255
        :return: class brightnessvalue member or None
        """
        if brightness is None:
            return self.brightnessvalue
        else:
            if brightness < 1:
                brightness = 1
        if brightness > 255:
            brightness = 255
        self.brightnessvalue = brightness

    def set_pixel_line_gradient(self, pixel1, pixel2, left_rgb_w, right_rgb_w, how_bright=None):
        """
        Create a gradient with two RGB colors between "pixel1" and "pixel2" (inclusive)

        :param pixel1: Index of starting pixel (inclusive)
        :param pixel2: Index of ending pixel (inclusive)
        :param left_rgb_w: Tuple of form (r, g, b) or (r, g, b, w) representing starting color
        :param right_rgb_w: Tuple of form (r, g, b) or (r, g, b, w) representing ending color
        :param how_bright: [default: None] Brightness of current interval. If None, use global brightness value
        :return: None
        """
        if pixel2 - pixel1 == 0:
            return
        right_pixel = max(pixel1, pixel2)
        left_pixel = min(pixel1, pixel2)

        with_W = len(left_rgb_w) == 4 and self.W_in_mode
        r_diff = right_rgb_w[0] - left_rgb_w[0]
        g_diff = right_rgb_w[1] - left_rgb_w[1]
        b_diff = right_rgb_w[2] - left_rgb_w[2]
        if with_W:
            w_diff = (right_rgb_w[3] - left_rgb_w[3])

        for i in range(right_pixel - left_pixel + 1):
            fraction = i / (right_pixel - left_pixel)
            red = round(r_diff * fraction + left_rgb_w[0])
            green = round(g_diff * fraction + left_rgb_w[1])
            blue = round(b_diff * fraction + left_rgb_w[2])
            # if it's (r, g, b, w)
            if with_W:
                white = round(w_diff * fraction + left_rgb_w[3])
                self.set_pixel(left_pixel + i, (red, green, blue, white), how_bright)
            else:
                self.set_pixel(left_pixel + i, (red, green, blue), how_bright)

    def set_pixel_line(self, pixel1, pixel2, rgb_w, how_bright=None):
        """
        Set an array of pixels starting from "pixel1" to "pixel2" (inclusive) to the desired color.

        :param pixel1: Index of starting pixel (inclusive)
        :param pixel2: Index of ending pixel (inclusive)
        :param rgb_w: Tuple of form (r, g, b) or (r, g, b, w) representing color to be used
        :param how_bright: [default: None] Brightness of current interval. If None, use global brightness value
        :return: None
        """
        if pixel2 >= pixel1:
            self.set_pixel(slice_maker[pixel1:pixel2 + 1], rgb_w, how_bright)

    def set_pixel(self, pixel_num, rgb_w, how_bright=None):
        """
        Set red, green and blue (+ white) value of pixel on position <pixel_num>
        pixel_num may be a 'slice' object, and then the operation is applied
        to all pixels implied by the slice (most useful when called via __setitem__)

        :param pixel_num: Index of pixel to be set or slice object representing multiple leds
        :param rgb_w: Tuple of form (r, g, b) or (r, g, b, w) representing color to be used
        :param how_bright: [default: None] Brightness of current interval. If None, use global brightness value
        :return: None
        """
        if how_bright is None:
            how_bright = self.brightness()
        sh_R, sh_G, sh_B, sh_W = self.shift
        bratio = how_bright / 255.0

        red = round(rgb_w[0] * bratio)
        green = round(rgb_w[1] * bratio)
        blue = round(rgb_w[2] * bratio)
        white = 0
        # if it's (r, g, b, w)
        if len(rgb_w) == 4 and self.W_in_mode:
            white = round(rgb_w[3] * bratio)

        pix_value = white << sh_W | blue << sh_B | red << sh_R | green << sh_G
        # set some subset, if pixel_num is a slice:
        if type(pixel_num) is slice:
            for i in range(*pixel_num.indices(self.num_leds)):
                self.pixels[i] = pix_value
        else:
            self.pixels[pixel_num] = pix_value

    def __setitem__(self, idx, rgb_w):
        """
        if npix is a Neopixel object,
        npix[10] = (0,255,0)        # <- sets #10 to green
        npix[15:21] = (255,0,0)     # <- sets 16,17 .. 20 to red
        npix[21:29:2] = (0,0,255)   # <- sets 21,23,25,27 to blue
        npix[1::2] = (0,0,0)        # <- sets all odd pixels to 'off'
        (the 'slice' cases pass idx as a 'slice' object, and
        set_pixel processes the slice)

        :param idx: Index can either be indexing number or slice
        :param rgb_w: Tuple of form (r, g, b) or (r, g, b, w) representing color to be used
        :return:
        """
        self.set_pixel(idx, rgb_w)

    def colorHSV(self, hue, sat, val):
        """
        Converts HSV color to rgb tuple and returns it.
        The logic is almost the same as in Adafruit NeoPixel library:
        https://github.com/adafruit/Adafruit_NeoPixel so all the credits for that
        go directly to them (license: https://github.com/adafruit/Adafruit_NeoPixel/blob/master/COPYING)

        :param hue: Hue component. Should be on interval 0..65535
        :param sat: Saturation component. Should be on interval 0..255
        :param val: Value component. Should be on interval 0..255
        :return: (r, g, b) tuple
        """
        if hue >= 65536:
            hue %= 65536

        hue = (hue * 1530 + 32768) // 65536
        if hue < 510:
            b = 0
            if hue < 255:
                r = 255
                g = hue
            else:
                r = 510 - hue
                g = 255
        elif hue < 1020:
            r = 0
            if hue < 765:
                g = 255
                b = hue - 510
            else:
                g = 1020 - hue
                b = 255
        elif hue < 1530:
            g = 0
            if hue < 1275:
                r = hue - 1020
                b = 255
            else:
                r = 255
                b = 1530 - hue
        else:
            r = 255
            g = 0
            b = 0

        v1 = 1 + val
        s1 = 1 + sat
        s2 = 255 - sat

        r = ((((r * s1) >> 8) + s2) * v1) >> 8
        g = ((((g * s1) >> 8) + s2) * v1) >> 8
        b = ((((b * s1) >> 8) + s2) * v1) >> 8

        return r, g, b

    def rotate_left(self, num_of_pixels=None):
        """
        Rotate <num_of_pixels> pixels to the left

        :param num_of_pixels: Number of pixels to be shifted to the left. If None, it shifts for 1.
        :return: None
        """
        if num_of_pixels is None:
            num_of_pixels = 1
        self.pixels = self.pixels[num_of_pixels:] + self.pixels[:num_of_pixels]

    def rotate_right(self, num_of_pixels=None):
        """
        Rotate <num_of_pixels> pixels to the right

        :param num_of_pixels: Number of pixels to be shifted to the right. If  None, it shifts for 1.
        :return: None
        """
        if num_of_pixels is None:
            num_of_pixels = 1
        num_of_pixels = -1 * num_of_pixels
        self.pixels = self.pixels[num_of_pixels:] + self.pixels[:num_of_pixels]

    def show(self):
        """
        Send data to led-strip, making all changes on leds have an effect.
        This method should be used after every method that changes the state of leds or after a chain of changes.
        :return: None
        """
        # If mode is RGB, we cut 8 bits of, otherwise we keep all 32
        cut = 8
        if self.W_in_mode:
            cut = 0
        sm_put = self.sm.put
        for pixval in self.pixels:
            sm_put(pixval, cut)
        time.sleep(self.delay)

    def fill(self, rgb_w, how_bright=None):
        """
        Fill the entire strip with color rgb_w

        :param rgb_w: Tuple of form (r, g, b) or (r, g, b, w) representing color to be used
        :param how_bright: [default: None] Brightness of current interval. If None, use global brightness value
        :return: None
        """
        # set_pixel over all leds.
        self.set_pixel(slice_maker[:], rgb_w, how_bright)

    def clear(self):
        """
        Clear the entire strip, i.e. set every led color to 0.

        :return: None
        """
        self.pixels = array.array("I", [0] * self.num_leds)