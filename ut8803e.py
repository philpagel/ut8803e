#! /bin/env python3
"""
Talk to a UNI-T UT8803E bench multimeter
"""

import sys, time, threading
from collections import deque
import click, cp2110
import construct as C


@click.command()
@click.option("--devno", "-d", default=0, help="Device to use (default=0)")
@click.argument("cmd")
def main(devno, cmd):
    """
Commands:

        log             start logging data\n
        get_ID          get instrument id\n
        brightness      change display brightness (3 steps)\n
        select          press `select` button\n
        range_manual    switch to next manual range    \n
        range_auto      set auto range\n
        minmax          set/toggle min/max mode\n
        exitminmax      exit min/max mode\n
        rel             set relative mode\n
        d_val           transistor D value \n
        q_val           transistor Q value\n
        r_val           transistor resitance\n
        exit_dqr        exit DQR mode
"""

    # connect to device    
    ut = ut8000()

    # commands
    if cmd == "log":
        ut.streamparser()
        #logger(ut)
    elif cmd not in ut.cmd_bytes:
        sys.exit(f"unknown command '{cmd}'")
    else:
        ut.send_request(cmd)


def logger(ut):

    for dat in ut:
        cs = sum(dat[:-2])
        try:
            dat = ut.package.parse(dat)

            if cs == dat.checksum:
                print(f"{time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())}", dat)
            else:
                print("   checksum mismatch")
        except C.ConstError:
                print("  ConstError")


class ut8000:
    "Device class for uni-t ut8xxx bench multimeters"

    cmd_bytes = {
            "get_ID"        : b"\x58\x00",
            "hold"          : b"\x46\x00",
            "brightness"    : b"\x47\x00",
            "select"        : b"\x48\x00",
            "range_manual"  : b"\x49\x00",
            "range_auto"    : b"\x4a\x00",
            "minmax"        : b"\x4b\x00",
            "exitminmax"    : b"\x4c\x00",
            "rel"           : b"\x4d\x00",
            "d_val"         : b"\x4e\x00",
            "q_val"         : b"\x4f\x00",
            "r_val"         : b"\x51\x00",
            "exit_dqr"      : b"\x50\x00",
            "confirm"       : b"\x5a\x00",
            }

    unit = ["V",
            "V",
            "µA",
            "mA",
            "A",
            "µA",
            "mA",
            "A",
            "Ohm",
            "",
            "",
            "Inductance L",
            "Inductance Q",
            "Inductance R",
            "Capacitance C",
            "Capacitance D",
            "Capacitance R",
            "Triode hFE",
            "Thyrisor SCR",
            "C",
            "F",
            "Hz",
            "%",
            ]
    mode = ["AC Voltage",
            "DC Voltage",
            "AC Current",
            "AC Current",
            "AC Current",
            "DC Current",
            "DC Current" ,
            "DC Current",
            "Resistance",
            "Continuity",
            "Diode",
            "Inductance L",
            "Inductance Q",
            "Inductance R",
            "Capacitance C",
            "Capacitance D",
            "Capacitance R",
            "Triode hFE",
            "Thyrisor SCR",
            "Temp",
            "Temp",
            "Freq",
            "Duty cycle",
            ]

    # package definitions

    package = C.Struct(
            "signature" / C.Const(b"\xab\xcd"),
            "length"    / C.Rebuild(C.Int8ub, C.len_(C.this.payload)+2),
            "payload"   / C.Bytes(C.this.length-2),
            "checksum"  / C.Int16ub,
            )

    #package = C.Struct(
    #        "signature" / C.Const(b"\xab\xcd"),
    #        "payload"   / C.Prefixed(C.Int8ub, C.GreedyBytes),
    #        )

    #payload = C.Struct(
    #        "length"    / C.Bytes(1),
    #        "data"      / C.Bytes(C.this.length-2),
    #        "checksum"  / C.Int16ub,
    #        )

    # measurement data
    mdata = C.Struct(
            "rectype"   / C.Bytes(1),
            "mode"      / C.Int8ub,
            "range"     / C.Bytes(1),
            "value"     / C.Bytes(6),
            "unk0"      / C.Bytes(2),
            "stat1"     / C.Bytes(3),
            "unk2"      / C.Bytes(2)
            )

    # measurement flags
    stat1 = C.BitStruct(
            "unk0"      / C.Flag,
            "unk1"      / C.Flag,
            "unk2"      / C.Flag,
            "unk3"      / C.Flag,
            "unk4"      / C.Flag,
            "OL"        / C.Flag,
            "foo"       / C.Flag,
            "Hold"      / C.Flag,
            "unk5"      / C.Flag,
            "unk6"      / C.Flag,
            "unk7"      / C.Flag,
            "unk8"      / C.Flag,
            "unk9"      / C.Flag,
            "unk10"     / C.Flag,
            "manrange"  / C.Flag,
            "rel"       / C.Flag,
            "unk11"     / C.Flag,
            "unk12"     / C.Flag,
            "unk13"     / C.Flag,
            "unk14"     / C.Flag,
            "unk15"     / C.Flag, # range?
            "unk16"     / C.Flag, # range? 
            "max"       / C.Flag,
            "min"       / C.Flag
            )


    def __init__(self):
        self.iface = cp2110.CP2110Device()
        self.iface.set_uart_config(cp2110.UARTConfig(
                            baud=9600,
                            parity=cp2110.PARITY.NONE,
                            flow_control=cp2110.FLOW_CONTROL.DISABLED,
                            data_bits=cp2110.DATA_BITS.EIGHT,
                            stop_bits=cp2110.STOP_BITS.SHORT)
                          )
        self.iface.enable_uart()
        self.iface.purge_fifos()

        self.buf = bytearray()
        self.data = deque()
        self.ID = None

        # start background reader
        reader = threading.Thread(target=self.streamreader)
        reader.start()
        # start background parser
        parser = threading.Thread(target=self.streamparser)
        parser.start()


    def __del__(self):
        try:
            self.iface.close()
        except:
            pass


    def streamreader(self):
        "Continuously read from data stream"
        while True:
            self.buf.extend(self.iface.read())

    def streamparser(self):
        "continuously parse the stream"

        i = 0
        while True:
            i += 1
            # XXX inject get_ID requests for testing every now and then
            if i % 9 == 8:
                pass
                self.send_request("get_ID")
            if len(self.buf) >= 64:
                print("len:", len(self.buf))
                while not self.buf.startswith(b"\xab\xcd"):
                    print("shift")
                    del(self.buf[0])
                #if len(self.buf) <32:
                #    continue
                package = self.package.parse(self.buf)
                rawpackage = self.package.build(package)
                checksum = sum(rawpackage[:-2])
                print(package)
                if checksum != package["checksum"]:
                    print("Checksum mismatch")
                del(self.buf[:len(rawpackage)])
                self.data.append(package)
                print(f"packages: {len(self.data)}")


    def send_request(self, cmd):
        "send cmd request to the instrument"

        payload = self.cmd_bytes[cmd]
        length = len(payload) + 2
        package = self.package.build(
                dict(
                    length = length,
                    payload=payload,
                    checksum=sum(b"\xab\xcd" + length.to_bytes(1, "big") + payload),
                    ),
                )
        self.iface.write(package)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
