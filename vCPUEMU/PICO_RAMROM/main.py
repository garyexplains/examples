from machine import Pin
import time

# Hard coded to read from a.out
with open("a.out", mode='rb') as file: # b is important -> binary
    mainmem = bytearray(file.read())
    
COUNT = 0
addrpins_nums = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
datapins_nums = [27,26,22,21,20,19,18,17]
addrpins = []
datapins = []
clk_mon = Pin(16, Pin.IN, Pin.PULL_DOWN)
rwb = Pin(28, Pin.IN, Pin.PULL_DOWN)

def set_pins(p, d):
    for a in p:
        b = d & 0x01
        if(b == 1):
            a.on()
        else:
            a.off()
        d = (d >> 1)
        
def print_addr_rw_data(pin):
    global COUNT
    
    addr = 0
    data = 0
    for a in reversed(addrpins):
         addr = (addr << 1) + a.value()
    rwb_v = rwb.value()
    rwb_c = "W"
    if(rwb_v == 1):
        # When in the high state, the microprocessor is reading data from memory or I/O.
        for a in reversed(datapins):
            a.init(mode=Pin.OUT)
        set_pins(datapins, mainmem[addr])
        data = mainmem[addr]
        rwb_c = "R"
    else:
        for a in reversed(datapins):
            a.init(mode=Pin.IN)
        for a in reversed(datapins):
            data = (data << 1) + a.value()
            mainmem[addr] = data
            
    print(COUNT, "Addr:", '0x{:04x}'.format(addr), rwb_c, "Data:", '0x{:04x}'.format(data))
    COUNT = COUNT + 1

for n in addrpins_nums:
    addrpins.append(Pin(n, Pin.IN,Pin.PULL_DOWN))

for n in datapins_nums:
    datapins.append(Pin(n, Pin.IN,Pin.PULL_DOWN))

clk_mon.irq(print_addr_rw_data, Pin.IRQ_RISING)
print("Running...")