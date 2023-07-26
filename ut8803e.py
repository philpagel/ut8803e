#! /bin/env python3
"""
Talk to a UNI-T UT8803E bench multimeter
"""

import sys, time, datetime
import click, cp2110
import construct as C


@click.command()
@click.option("--debug", "-d", is_flag=True, default=False, help="Turn on debugging information")
@click.option("--period", "-p", default=None, help="Length of logging period [HH:MM:SS]. Max period: 23:59:59")
@click.argument("cmd")
def main(debug, cmd, period):
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

    if period:
        try:
            period = time.strptime(period, "%H:%M:%S")
        except ValueError:
            sys.exit(f"Invalid time format for option --period / -p ")
        period = 3600*period.tm_hour + 60*period.tm_min + period.tm_sec
    
    # connect to device    
    ut = ut8000()

    if cmd == "log":
        ut.streamparser(debug=debug, period=period)
    elif cmd == "get_ID":
        ut.streamparser(debug=debug, period=1, logging=False)
        print(f"Device-ID: {ut.ID}")
    elif cmd not in ut.cmd_bytes:
        sys.exit(f"unknown command '{cmd}'")
    else:
        ut.send_request(cmd)
        ut.send_request("confirm")


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

    # data package
    package = C.Struct(
            "signature" / C.Const(b"\xab\xcd"),
            "length"    / C.Rebuild(C.Int8ub, C.len_(C.this.payload)+2),
            "payload"   / C.Bytes(C.this.length-2),
            "checksum"  / C.Int16ub,
            )

    # measurement data
    mdata = C.Struct(
            "rectype"   / C.Bytes(1),
            "mode"      / C.Int8ub,
            "range"     / C.Bytes(1),
            "value"     / C.PaddedString(6, "utf8"),
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
        self.buf = bytearray()
        self.ID = None
        self.iface = cp2110.CP2110Device()
        
        # setup interface
        self.iface.set_uart_config(cp2110.UARTConfig(
                            baud=9600,
                            parity=cp2110.PARITY.NONE,
                            flow_control=cp2110.FLOW_CONTROL.DISABLED,
                            data_bits=cp2110.DATA_BITS.EIGHT,
                            stop_bits=cp2110.STOP_BITS.SHORT)
                          )
        self.iface.enable_uart()


    def __del__(self):
        try:
            self.iface.purge_fifos()
            self.iface.close()
        except:
            pass


    def streamparser(self, logging=True, debug=False, period=None):
        "Continuously read from data stream and parse it"
        
        if debug:
            print("Starting streamreader")

        self.iface.purge_fifos()
        self.send_request("get_ID")
        self.send_request("confirm")

        t0 = time.time()
        package_no = 0
        if logging:
            print("No,timestamp,value")
        while True:
            self.buf.extend(self.iface.read(63))

            if len(self.buf) >= 26:
                t = time.time()
                delta_t = t-t0

                # seek package signature
                while not self.buf.startswith(b"\xab\xcd"):
                    del(self.buf[0])
                    if debug:
                        print("shift", file=sys.stderr)
                if len(self.buf) < 26: 
                    continue

                package = self.package.parse(self.buf)
                rawpackage = self.package.build(package)
                checksum = sum(rawpackage[:-2])
                if checksum != package["checksum"]:
                    print("Checksum mismatch", file=sys.stderr)
                del(self.buf[:len(rawpackage)])

                # parse the payload
                if package["payload"].startswith(b"\x02"):
                    mvals = self.mdata.parse(package["payload"])
                elif package["payload"].startswith(b"\x00"):
                    self.ID = package["payload"][1:].decode("utf8")
                    continue
                else:
                    print(f"Unknown package type {hex(package['payload'][0])}. Skipping", file=sys.stderr)
                    continue
                
                if debug:
                    print(f"\npackage #{package_no}", file=sys.stderr)
                    print(f"t: {delta_t}s", file=sys.stderr)
                    print(f"buflen: {len(self.buf)}", file=sys.stderr)
                    print(package, file=sys.stderr)
                    print(mvals, file=sys.stderr)

                if logging:
                    print(",".join(
                        (str(x) for x in (
                            package_no,
                            datetime.datetime.fromtimestamp(t),
                            #time.strftime("%Y-%m-%dT%X", time.localtime(t)),
                            mvals["value"],
                        )
                        )
                    ))

                package_no += 1
                if period and delta_t >= period:
                    break


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


