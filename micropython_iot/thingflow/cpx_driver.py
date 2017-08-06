'''Circuit Playground Express (CPX) REPL driver

Run this module on a host computer with CPX plugged in a USB port::

    import cpx_driver

    cpx = cpx_driver.CPX()
    cpx.light  # Get light sensor data
'''

import serial
import itertools

max_brightness = 0.05

class Serial:
    '''Drive serial communication'''

    def __init__(self, dev_file):
        self.prompt = '>>> '
        self.serial = serial.Serial(dev_file, baudrate=115200, rtscts=True,
            timeout=0.01)

    def read(self):
        data = self.serial.readall().decode()
        if data[-len(self.prompt):] == self.prompt:
            data = data[:-len(self.prompt)]
        return data

    def write(self, data):
        self.serial.write((data + '\r\n').encode())
        self.serial.flush()
        self.serial.readline()

    def flush(self):
        self.serial.flush()
        data = self.serial.readall().decode()
        if data[-4:] != self.prompt:
            pass  # handle condition if we didn't get prompt


class CPX:
    '''Drive Circuit Playground'''
    neopixel_count = 10

    def __init__(self, dev_file='/dev/ttyACM0'):
        ''' SerialException conditions:
                Device or resource busy: '/dev/ttyACM0'
                No such file or directory: '/dev/ttyACM0'
        '''
        self.serial = Serial(dev_file)
        self.send_nores('')  # CPX require a new line to enter REPL
        self.send_nores('import analogio, digitalio, board')
        self.send_nores('light = analogio.AnalogIn(board.LIGHT)')
        self.send_nores('from neopixel_write import neopixel_write')
        self.send_nores('neopixel_pin = digitalio.DigitalInOut(board.NEOPIXEL)')
        self.send_nores('neopixel_pin.direction = digitalio.Direction.OUTPUT')
        self.send_nores('neopixel = lambda buf: neopixel_write(neopixel_pin, buf)')
        self.neopixel_buf = bytearray(self.neopixel_count * 3)  # 10 neopixels with 3 bytes per pixel

    def send_nores(self, line):
        self.serial.write(line)
        self.serial.read()

    def send_res(self, line):
        self.serial.write(line)
        return self.serial.read()

    def send_res_int(self, line):
        return int(self.send_res(line))

    @property
    def light(self):
        '''Get Light sensor data'''
        return self.send_res_int('light.value')

    def neopixel(self, rgb=None, pix_nr=None, buf=None):
        ''' Drive neopixels
            if no pix_nr is given, use rgb on all pixels
            use buf if no rgb or pix_nr are given'''
        if buf:  # Prepare buf for CPX  (it uses grb)
            buf = [i for i in buf]
            buf = tuple(itertools.chain(*zip(buf[1::3], buf[0::3], buf[2::3])))
        if not rgb and pix_nr is None and buf:
            self.send_nores('neopixel(bytearray(%s))' % str(buf))
            self.neopixel_buf = bytearray(buf)
        elif rgb and pix_nr is None:
            rgb = (rgb[1], rgb[0], rgb[2])
            self.send_nores('neopixel(bytearray(%s*%s))' % (
                str(rgb), self.neopixel_count))
            self.neopixel_buf = bytearray(rgb * self.neopixel_count)
        elif rgb and pix_nr is not None:
            rgb = [rgb[1], rgb[0], rgb[2]]
            buf = [i for i in self.neopixel_buf]
            buf = buf[:pix_nr*3] + rgb + buf[(pix_nr+1)*3:]
            self.send_nores('neopixel(bytearray(%s))' % str(buf))
            self.neopixel_buf = bytearray(buf)


def clamp(n, min, max):
    '''Return   n if min <= n <= max
              min if n < min
              max if n > max
    '''
    return sorted((min, n, max))[1]


def wheel(level):
    '''    if level < 128:
        return (255-level*2, level*2, 0)
    else:
        level -= 128
        return (0, 255-level*2, level*2)

    '''
    if level < 85:
        return (level*3, 0, 0)
    elif level < 170:
        level -= 85
        return (255-level*3, level*3, 0)
    else:
        level -= 170
        return (0, 255-level*3, level*3)


def level_to_rgb(level, brightness=1):
    '''Transform level to rgb for strip sensor
       0 <= level <= 255'''
    brightness = clamp(brightness, 0, 1)
    level = clamp(level, 0, 255)
    rgb = tuple(int(c*brightness*max_brightness) for c in wheel(level))
    return rgb


def vumeter(level):
    '''Return a vumeter buffer based on level'''
    coef = 255/CPX.neopixel_count  # maximun color-level for one neopixel
    levels = [int(coef*(i+1)) if coef*i < level else 0 for i in range(10)]
    buf = bytearray(sum((level_to_rgb(l, level/255) for l in levels), ()))
    if buf[0] == 0 and 18 < level:  # Ensure the first pixel is reasonable lit
        buf[0] = 1
    return buf
