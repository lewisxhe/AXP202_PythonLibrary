import time
import axp202
import machine

GPS_RX_PIN = 34
GPS_TX_PIN = 12

axp = axp202.PMU(address=axp202.AXP192_SLAVE_ADDRESS)
# axp.setDCDC1Voltage(3300) # esp32 core VDD    3v3
axp.setLDO2Voltage(3300)   # T-Beam LORA VDD   3v3
axp.setLDO3Voltage(3300)   # T-Beam GPS  VDD    3v3
axp.enablePower(axp202.AXP192_LDO3)
axp.enablePower(axp202.AXP192_LDO2)


uart = machine.UART(2, rx=GPS_RX_PIN, tx=GPS_TX_PIN, baudrate=9600, bits=8, parity=None, stop=1, timeout=1500, buffer_size=1024, lineend='\r\n')
gps = machine.GPS(uart)
gps.init()
gps.startservice()
gps.service()
while True:
    gps.getdata()
    time.sleep(1)
