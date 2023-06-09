# *****************************************************************************
# * | File        :	  Pico_ePaper-2.9-B.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2021-03-16
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from machine import Pin, SPI
import framebuf
import utime

import network
from time import sleep
import urequests as requests
secrets = {
    'ssid':'CountryRoad',
    'pw':'NjAmFmAmPa',
    'ical-test':'https://postman-echo.com/get',
    'ical': 'https://outlook.office365.com/owa/calendar/8f8c921f27c34f9f94f7e7425e1bb121@unitestudents.com/d921004e48c8411894654d8662454ecb15100811438411454638/calendar.ics'
}



# Display resolution
EPD_WIDTH = 128
EPD_HEIGHT = 296

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13


class EPD_2in9_B:
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer_black = bytearray(self.height * self.width // 8)
        self.buffer_red = bytearray(self.height * self.width // 8)
        self.imageblack = framebuf.FrameBuffer(
            self.buffer_black, self.width, self.height, framebuf.MONO_HLSB
        )
        self.imagered = framebuf.FrameBuffer(
            self.buffer_red, self.width, self.height, framebuf.MONO_HLSB
        )
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print("busy")
        self.send_command(0x71)
        while self.digital_read(self.busy_pin) == 0:
            self.send_command(0x71)
            self.delay_ms(10)
        print("busy release")

    def TurnOnDisplay(self):
        self.send_command(0x12)
        self.ReadBusy()

    def init(self):
        print("init")
        self.reset()
        self.send_command(0x04)
        self.ReadBusy()  # waiting for the electronic paper IC to release the idle signal

        self.send_command(0x00)  # panel setting
        self.send_data(0x0F)  # LUT from OTP,128x296
        self.send_data(
            0x89
        )  # Temperature sensor, boost and other related timing settings

        self.send_command(0x61)  # resolution setting
        self.send_data(0x80)
        self.send_data(0x01)
        self.send_data(0x28)

        self.send_command(0x50)  # VCOM AND DATA INTERVAL SETTING
        self.send_data(0x77)  # WBmode:VBDF 17|D7 VBDW 97 VBDB 57
        # WBRmode:VBDF F7 VBDW 77 VBDB 37  VBDR B7
        return 0

    def display(self):
        self.send_command(0x10)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(self.buffer_black[i + j * int(self.width / 8)])
        self.send_command(0x13)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(self.buffer_red[i + j * int(self.width / 8)])

        self.TurnOnDisplay()

    def Clear(self, colorblack, colorred):
        self.send_command(0x10)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(colorblack)
        self.send_command(0x13)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(colorred)

        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x02)  # power off
        self.ReadBusy()
        self.send_command(0x07)  # deep sleep
        self.send_data(0xA5)

        self.delay_ms(2000)
        self.module_exit()


def http_get(url):
    import socket
    import ssl
    _, _, host, path = url.split('/', 3)
    addr = socket.getaddrinfo(host, 443)[0]
    print(addr)
    s = socket.socket(addr[0], addr[1], addr[2])
    s.connect(addr[-1])
    s = ssl.wrap_socket(s, server_hostname=host)
    #s.connect(('192.168.0.25', 8080))
    request = 'GET /%s HTTP/1.1\r\nHost: %s\r\nUser-Agent: PICO\r\nAccept: */*\r\n\r\n' % (path, host)
    #print(request)
    s.write(bytes(request, 'utf8'))
    while True:
        data = s.readline()
        if data:
            print(str(data, 'utf8'), end='')
        else:
            break
    s.close()
    print("closed")
if __name__ == "__main__":
    epd = EPD_2in9_B()
#    print("start clear")
#    epd.Clear(0xFF, 0xFF)
#    print("clear done")
#    epd.imageblack.fill(0xFF)
#    epd.imagered.fill(0xFF)
#    epd.imageblack.text("Connecting", 0, 10, 0x00)
#    epd.display()
    print("starting networking")
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        wlan.active(True)
        wlan.connect(secrets['ssid'], secrets['pw'])
        while not wlan.isconnected():
            print('Waiting for connection...')
            sleep(1)

    print(wlan.ifconfig())
    #epd.imageblack.text("Connected, IP:", 0, 10, 0x00)
    #epd.imagered.text(wlan.ifconfig()[0], 0, 55, 0x00)

    #epd.display()
    print("displayed ip")
    print("requesting " + secrets['ical'])
    headers = {
        "user-agent": "insomnia/2023.1.0",
		"accept": "*/*"
    }
    
    http_get(secrets['ical'])
 
#    response = requests.get(secrets['ical'], headers=headers)
#    print(response.content)
#    response.close()
