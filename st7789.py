import time
import ustruct
import framebuf
from micropython import const
from machine import Pin, SPI

OPEN_AXP202 = True

if OPEN_AXP202:
    import axp202


TFT_RST_PIN = const(0)
TFT_LED_PIN = const(12)
TFT_DC_PIN = const(27)
TFT_CS_PIN = const(5)
TFT_CLK_PIN = const(18)
TFT_MISO_PIN = const(2)
TFT_MOSI_PIN = const(19)

_CHUNK = const(1024)  # maximum number of pixels per spi write

TFT_RAMWR = const(0x2C)
TFT_SWRST = const(0x01)
ST7789_SLPOUT = const(0x11)
ST7789_NORON = const(0x13)
ST7789_MADCTL = const(0x36)
TFT_MAD_COLOR_ORDER = const(0x08)
ST7789_COLMOD = const(0x3A)
ST7789_PORCTRL = const(0xB2)
ST7789_GCTRL = const(0xB7)
ST7789_VCOMS = const(0xBB)
ST7789_LCMCTRL = const(0xC0)
ST7789_VDVVRHEN = const(0xC2)
ST7789_VRHS = const(0xC3)
ST7789_VDVSET = const(0xC4)
ST7789_FRCTR2 = const(0xC6)
ST7789_PWCTRL1 = const(0xD0)
ST7789_PVGAMCTRL = const(0xD0)
ST7789_NVGAMCTRL = const(0xE1)
ST7789_INVON = const(0x21)
ST7789_CASET = const(0x2A)
ST7789_RASET = const(0x2B)
ST7789_DISPON = const(0x29)


class ST7789(object):

    width = 240
    height = 240

    def __init__(self, spi, cs, dc, rst):
        self.spi = spi
        self.cs = cs 
        self.dc = dc 
        self.rst = rst
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        if self.rst is not None:
            self.rst.init(self.rst.OUT, value=0)
        self._buf = bytearray(_CHUNK * 2)
        # default white foregraound, black background
        self._colormap = bytearray(b'\x00\x00\xFF\xFF')

        self.init_pins()
        if self.rst is not None:
            self.reset()
        else:
            self.soft_reset()
        self.init()

    def reset(self):
        self.rst(0)
        time.sleep(0.5)
        self.rst(1)
        time.sleep(0.5)

    def init_pins(self):
        pass

    def soft_reset(self):
        self._write(TFT_SWRST)   # Sleep out
        time.sleep(0.5)

    def init(self):

        self._write(ST7789_SLPOUT)   # Sleep out
        time.sleep_ms(120)

        self._write(ST7789_NORON)    # Normal display mode on

        #------------------------------display and color format setting--------------------------------#
        self._write(ST7789_MADCTL)
        # self._data(0x00)
        self._data(TFT_MAD_COLOR_ORDER)

        # JLX240 display datasheet
        self._write(0xB6)
        self._data(0x0A)
        self._data(0x82)

        self._write(ST7789_COLMOD)
        self._data(0x55)
        time.sleep_ms(10)

        #--------------------------------ST7789V Frame rate setting----------------------------------#
        self._write(ST7789_PORCTRL)
        self._data(0x0c)
        self._data(0x0c)
        self._data(0x00)
        self._data(0x33)
        self._data(0x33)

        self._write(ST7789_GCTRL)      # Voltages: VGH / VGL
        self._data(0x35)

        #---------------------------------ST7789V Power setting--------------------------------------#
        self._write(ST7789_VCOMS)
        self._data(0x28)        # JLX240 display datasheet

        self._write(ST7789_LCMCTRL)
        self._data(0x0C)

        self._write(ST7789_VDVVRHEN)
        self._data(0x01)
        self._data(0xFF)

        self._write(ST7789_VRHS)       # voltage VRHS
        self._data(0x10)

        self._write(ST7789_VDVSET)
        self._data(0x20)

        self._write(ST7789_FRCTR2)
        self._data(0x0f)

        self._write(ST7789_PWCTRL1)
        self._data(0xa4)
        self._data(0xa1)

        #--------------------------------ST7789V gamma setting---------------------------------------#
        self._write(ST7789_PVGAMCTRL)
        self._data(0xd0)
        self._data(0x00)
        self._data(0x02)
        self._data(0x07)
        self._data(0x0a)
        self._data(0x28)
        self._data(0x32)
        self._data(0x44)
        self._data(0x42)
        self._data(0x06)
        self._data(0x0e)
        self._data(0x12)
        self._data(0x14)
        self._data(0x17)

        self._write(ST7789_NVGAMCTRL)
        self._data(0xd0)
        self._data(0x00)
        self._data(0x02)
        self._data(0x07)
        self._data(0x0a)
        self._data(0x28)
        self._data(0x31)
        self._data(0x54)
        self._data(0x47)
        self._data(0x0e)
        self._data(0x1c)
        self._data(0x17)
        self._data(0x1b)
        self._data(0x1e)

        self._write(ST7789_INVON)

        self._write(ST7789_CASET)    # Column address set
        self._data(0x00)
        self._data(0x00)
        self._data(0x00)
        self._data(0xE5)    # 239

        self._write(ST7789_RASET)    # Row address set
        self._data(0x00)
        self._data(0x00)
        self._data(0x01)
        self._data(0x3F)    # 319

        # /

        time.sleep_ms(120)

        self._write(ST7789_DISPON)  # Display on
        time.sleep_ms(120)

    def _write(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc(1)
        self.cs(0)
        if type(data) == type(1):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs(1)

    def _writeblock(self, x0, y0, x1, y1, data=None):
        self._write(ST7789_CASET, ustruct.pack(">HH", x0, x1))
        self._write(ST7789_RASET, ustruct.pack(">HH", y0, y1))
        self._write(TFT_RAMWR, data)

    def fill_rectangle(self, x, y, w, h, color=None):
        x = min(self.width - 1, max(0, x))
        y = min(self.height - 1, max(0, y))
        w = min(self.width - x, max(1, w))
        h = min(self.height - y, max(1, h))
        if color:
            color = ustruct.pack(">H", color)
        else:
            color = self._colormap[0:2]  # background
        for i in range(_CHUNK):
            self._buf[2*i] = color[0]
            self._buf[2*i+1] = color[1]
        chunks, rest = divmod(w * h, _CHUNK)
        self._writeblock(x, y, x + w - 1, y + h - 1, None)
        if chunks:
            for count in range(chunks):
                self._data(self._buf)
        if rest != 0:
            mv = memoryview(self._buf)
            self._data(mv[:rest*2])

    def blit(self, bitbuff, x, y, w, h):
        x = min(self.width - 1, max(0, x))
        y = min(self.height - 1, max(0, y))
        w = min(self.width - x, max(1, w))
        h = min(self.height - y, max(1, h))
        chunks, rest = divmod(w * h, _CHUNK)
        self._writeblock(x, y, x + w - 1, y + h - 1, None)
        written = 0
        for iy in range(h):
            for ix in range(w):
                index = ix+iy*w - written
                if index >= _CHUNK:
                    self._data(self._buf)
                    written += _CHUNK
                    index -= _CHUNK
                c = bitbuff.pixel(ix, iy)
                self._buf[index*2] = self._colormap[c*2]
                self._buf[index*2+1] = self._colormap[c*2+1]
        rest = w*h - written
        if rest != 0:
            mv = memoryview(self._buf)
            self._data(mv[:rest*2])

if OPEN_AXP202:
    a = axp202.PMU()
    a.setChgLEDMode(axp202.AXP20X_LED_BLINK_1HZ)
    a.enablePower(axp202.AXP202_LDO2)
    a.setLDO2Voltage(3300)
bl = Pin(TFT_LED_PIN, Pin.OUT)
bl.value(1)

spi = SPI(baudrate=40000000, miso=Pin(TFT_MISO_PIN), mosi=Pin(
    TFT_MOSI_PIN, Pin.OUT), sck=Pin(TFT_CLK_PIN, Pin.OUT))

display = ST7789(spi, cs=Pin(TFT_CS_PIN), dc=Pin(TFT_DC_PIN), rst=None)

while True:
    display.fill_rectangle(0, 0, display.width, display.height, 0x0000)
    time.sleep(1)
    display.fill_rectangle(0, 0, display.width, display.height, 0xFF00)
    time.sleep(1)
    display.fill_rectangle(0, 0, display.width, display.height, 0xF800)
    time.sleep(1)
