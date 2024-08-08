# https://gist.github.com/shawwwn/91cc8979e33e82af6d99ec34c38195fb
# µPing (MicroPing) for MicroPython
# copyright (c) 2018 Shawwwn <shawwwn1@gmail.com>
# License: MIT

# Internet Checksum Algorithm
# Author: Olav Morken
# https://github.com/olavmrk/python-ping/blob/master/ping.py
# @data: bytes
def checksum(data):
    if len(data) & 0x1: # Odd number of bytes
        data += b'\0'
    cs = 0
    for pos in range(0, len(data), 2):
        b1 = data[pos]
        b2 = data[pos + 1]
        cs += (b1 << 8) + b2
    while cs >= 0x10000:
        cs = (cs & 0xffff) + (cs >> 16)
    cs = ~cs & 0xffff
    return cs

def ping(host, count=4, timeout=5000, interval=10, quiet=False, size=64):
    import utime
    import uselect
    import uctypes
    import usocket
    import ustruct
    import urandom

    # prepare packet
    assert size >= 16, "pkt size too small"
    pkt = b'Q'*size
    pkt_desc = {
        "type": uctypes.UINT8 | 0,
        "code": uctypes.UINT8 | 1,
        "checksum": uctypes.UINT16 | 2,
        "id": uctypes.UINT16 | 4,
        "seq": uctypes.INT16 | 6,
        "timestamp": uctypes.UINT64 | 8,
    } # packet header descriptor
    h = uctypes.struct(uctypes.addressof(pkt), pkt_desc, uctypes.BIG_ENDIAN)
    h.type = 8 # ICMP_ECHO_REQUEST
    h.code = 0
    h.checksum = 0
    h.id = urandom.getrandbits(16)
    h.seq = 1

    # init socket
    sock = usocket.socket(usocket.AF_INET, usocket.SOCK_RAW, 1)
    sock.setblocking(0)
    sock.settimeout(timeout/1000)
    addr = usocket.getaddrinfo(host, 1)[0][-1][0] # ip address
    sock.connect((addr, 1))
    not quiet and print("PING %s (%s): %u data bytes" % (host, addr, len(pkt)))

    seqs = list(range(1, count+1)) # [1,2,...,count]
    c = 1
    t = 0
    n_trans = 0
    n_recv = 0
    finish = False
    while t < timeout:
        if t==interval and c<=count:
            # send packet
            h.checksum = 0
            h.seq = c
            h.timestamp = utime.ticks_us()
            h.checksum = checksum(pkt)
            if sock.send(pkt) == size:
                n_trans += 1
                t = 0 # reset timeout
            else:
                seqs.remove(c)
            c += 1

        # recv packet
        while 1:
            socks, _, _ = uselect.select([sock], [], [], 0)
            if socks:
                resp = socks[0].recv(4096)
                resp_mv = memoryview(resp)
                h2 = uctypes.struct(uctypes.addressof(resp_mv[20:]), pkt_desc, uctypes.BIG_ENDIAN)
                # TODO: validate checksum (optional)
                seq = h2.seq
                if h2.type==0 and h2.id==h.id and (seq in seqs): # 0: ICMP_ECHO_REPLY
                    t_elasped = (utime.ticks_us()-h2.timestamp) / 1000
                    ttl = ustruct.unpack('!B', resp_mv[8:9])[0] # time-to-live
                    n_recv += 1
                    not quiet and print("%u bytes from %s: icmp_seq=%u, ttl=%u, time=%f ms" % (len(resp), addr, seq, ttl, t_elasped))
                    seqs.remove(seq)
                    if len(seqs) == 0:
                        finish = True
                        break
            else:
                break

        if finish:
            break

        utime.sleep_ms(1)
        t += 1

    # close
    sock.close()
    ret = (n_trans, n_recv)
    not quiet and print("%u packets transmitted, %u packets received" % (n_trans, n_recv))
    return (n_trans, n_recv)

"""
Copyright (c) 2024 Gary Sims

MIT License
SPDX-License-Identifier: MIT
"""

from time import sleep
import network
import time
from machine import Pin, RTC, SPI

interval = 180

def test_by_ping(host, ledok, ledbad):
    ledok.off()
    ledbad.off()
    ping_sent, ping_recv = ping(host, quiet=True)
    if ping_sent > 0 and ping_recv > 0:
        ledok.on()
        ledbad.off()
    else:
        ledok.off()
        ledbad.on()
    
ledi = Pin("LED", Pin.OUT)
ledi.off()

site1 = "8.8.8.8"
site1ok = Pin(0, Pin.OUT)
site1ok.on()
site1bad = Pin(1, Pin.OUT)
site1bad.on()

site2 = "192.168.1.1"
site2ok = Pin(6, Pin.OUT)
site2ok.on()
site2bad = Pin(7, Pin.OUT)
site2bad.on()

site3 = "192.168.1.21"
site3ok = Pin(8, Pin.OUT)
site3ok.on()
site3bad = Pin(9, Pin.OUT)
site3bad.on()

heartbeatled = Pin(2, Pin.OUT)
heartbeatled.off()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SSID', 'PASSWORD')

while not wlan.isconnected() and wlan.status() >= 0:
    print("Waiting to connect:")
    time.sleep(1)

ledi.on()
heartbeatled.on()

site1ok.off()
site1bad.off()
site2ok.off()
site2bad.off()
site3ok.off()
site3bad.off()

c = interval
while True:
    ledi.toggle()
    heartbeatled.toggle()
    c = c + 1
    if c > interval:
        test_by_ping(site1, site1ok, site1bad)
        test_by_ping(site2, site2ok, site2bad)
        test_by_ping(site3, site3ok, site3bad)
        c = 0
    sleep(1)
