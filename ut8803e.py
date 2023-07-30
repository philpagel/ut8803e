#! /bin/env python3
"""
Talk to a UNI-T UT8803E bench multimeter
"""

import sys, time, datetime, json
from collections import OrderedDict, deque
import click, cp2110
import construct as C


@click.command()
@click.option("--period", "-p", default=None, help="Length of logging period [HH:MM:SS]. Max period: 23:59:59")
@click.option("--interval", "-i", default=0, help="Logging interval [s]")
@click.option("--format", "-f", default="csv", help="Logging data format (csv/json/reversing)")
@click.option("--full", is_flag=True, default=False, help="show value even if ERR or OL apply")
@click.argument("cmd")
def main(cmd, period, interval, format, full):
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
        d_val           capacitor D value \n
        q_val           inductance Q value\n
        r_val           inductance/capacitor resistance\n
        exit_dqr        exit DQR mode
"""

    if period:
        try:
            period = time.strptime(period, "%H:%M:%S")
        except ValueError:
            sys.exit(f"Invalid time format for option --period / -p ")
        period = 3600*period.tm_hour + 60*period.tm_min + period.tm_sec
    
    # connect to device    
    ut = ut8000(full=full, format=format)

    if cmd == "log":
        ut.streamreader(period=period, interval=interval)
    elif cmd == "get_ID":
        ut.streamreader(period=1, logging=False)
        print(f"Device-ID: {ut.ID}")
    elif cmd not in ut.cmd_bytes:
        sys.exit(f"unknown command '{cmd}'")
    else:
        ut.send_request(cmd)
        ut.send_request("confirm")


def strcmp(s1, s2):
    "highlight differences of two stings"

    l = min(len(s1), len(s2))
    ret = ""
    for i in range(l):
        ret += " " if s1[i] == s2[i] else "|"
    return ret


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
            #"unk1"          : b"\x58\x00", # sent by windows software at the begining
            }

    # modes
    mode = [{
                "name" : "AC Voltage",     
                "unit" : ["mV", "V", "V", "V", "V"], 
                "range" : ["600mV", "6V", "60V", "600V", "750V"],
             },
            {
                "name" : "DC Voltage",	    
                "unit" : ["mV", "V", "V", "V", "V", "V"], 
                "range" : ["600mV", "6V", "60V", "600V", "1000V"],
            },
            {
                "name" : "AC Current µA",  
                "unit" : ["µA", "ma"], 
                "range" : ["600µA", "6mA"],
            },
            {
                "name" : "AC Current mA",  
                "unit" : ["ma", "mA"], 
                "range" : ["60mA", "600mA"],
            },
            {
                "name" : "AC Current A",   
                "unit" : ["A"],
                "range" : ["10A"],
            },
            {
                "name" : "DC Current µA",  
                "unit" : ["µA", "mA"],
                "range" : ["600µA", "6mA"],
            },
            {
                "name" : "DC Current mA",
                "unit" : ["mA", "mA"], 
                "range" : ["60mA", "600mA"],
            },
            {
                "name" : "DC Current A",   
                "unit" : ["A"],
                "range" : ["10A"],
            },
            {
                "name" : "Resistance",	    
                "unit" : ["Ω", "kΩ", "kΩ", "kΩ", "MΩ", "MΩ"], 
                "range" : ["600Ω", "6kΩ", "60kΩ", "600kΩ", "6MΩ", "60MΩ"],
            },
            {
                "name" : "Continuity",	    
                "unit" : [""], 
                "range" : ["NA"] 
            },
            {
                "name" : "Diode",	        
                "unit" : ["ΔV"], 
                "range" : ["NA"] 
            },
            {
                "name" : "Inductance L",   
                "unit" : ["µH", "mH", "mH", "mH", "H", "H", "H"], 
                "range" : ["600µH", "6mH", "60mH", "600mH", "6H", "60H", "100H"] 
            },
            {
                "name" : "Inductance Q",   
                "unit" : [""], 
                "range" : ["NA"] 
            },
            {
                "name" : "Inductance R",   
                "unit" : ["Ω", "Ω", "kΩ", "kΩ", "kΩ", "MΩ"], 
                "range" : ["60Ω", "600Ω", "6kΩ", "60kΩ", "600kΩ", "2MΩ"], 
            },
            {
                "name" : "Capacitance C",  
                "unit" : ["nF", "nF", "F", "µF", "µF", "µF", "mF"], 
                "range" : ["6nF", "60nF", "600nF", "6µF", "60µF", "600µF", "6mF"],
            },
            {
                "name" : "Capacitance D",  
                "unit" : [""] * 5, 
                "range" : ["NA0", "NA1", "NA2", "NA3","NA4"] 
            }, # XXX FIXME: what do the ranges mean?
            {
                "name" : "Capacitance R",  
                "unit" : ["Ω", "Ω", "kΩ", "kΩ", "kΩ", "MΩ"], 
                "range" : ["60Ω", "600Ω", "6kΩ", "60kΩ", "600kΩ", "2MΩ"],
            },
            {
                "name" : "Triode hFE",	    
                "unit" : [""] * 5, 
                "range" : ["NA0", "NA1", "NA2", "NA3","NA4"],
            }, # XXX FIXME meaning of ranges?
            {
                "name" : "Thyrisor SCR",   
                "unit" : [""] * 5, 
                "range" : ["NA0", "NA1", "NA2", "NA3","NA4"],
            }, # XXX FIXME
            {
                "name" : "Temp °C",	    
                "unit" : ["°C"] * 3, 
                "range" : ["-40 - 0°C", "0 - 400°C", "400 - 1000°C"],
            },
            {
                "name" : "Temp F",	        
                "unit" : ["°F"] * 3,
                "range" : ["-40 - 32°F", "32 - 752°F", "752 - 1832°F"] 
            },
            {
                "name" : "Freq",	        
                "unit" : ["Hz", "kHz", "kHz", "kHz", "MHz", "MHz"], 
                "range" : ["600Hz", "6kHz", "60kHz", "600kHz", "6MHz", "20MHz"], 
            },
            {
                "name" : "Duty cycle",	    
                "unit" : ["%"] * 6, 
                "range" : ["600Hz", "6kHz", "60kHz", "600kHz", "6MHz", "20MHz"] 
            },
            ]

    prefix = ["n", 'µ', 'm', '', 'k', 'M', 'G']
    prefix = ["M", "", '', '', '', '', '', 'k']

    # data package
    package = C.Struct(
            "signature" / C.Const(b"\xab\xcd"),
            "length"    / C.Rebuild(C.Int8ub, C.len_(C.this.payload)+2),
            "payload"   / C.Bytes(C.this.length-2),
            "checksum"  / C.Int16ub,
            )

    # measurement data payload
    mdata = C.Struct(
            "rectype"   / C.Bytes(1),
            "mode"      / C.Int8ub,
            "range"     / C.PaddedString(1, "ascii"),
            "value"     / C.PaddedString(6, "ascii"),
            "stat"      / C.Bytes(7),
            )

    # measurement flags
    stat = C.BitStruct(
            "unk00"         / C.Flag, 
            "unk01"         / C.Flag,
            "unk02"         / C.Flag,
            "unk03"         / C.Flag,
            "unk04"         / C.Flag, # XXX bargraph length?
            "unk05"         / C.Flag,
            "unk06"         / C.Flag,
            "unk07"         / C.Flag,

            "unk10"         / C.Flag,
            "unk11"         / C.Flag,
            "unk12"         / C.Flag,
            "unk13"         / C.Flag,
            "unk14"         / C.Flag,
            "unk15"         / C.Flag,
            "unk16"         / C.Flag,
            "serpal"        / C.Flag, # XXX: confirm

            "unk20"         / C.Flag,
            "unk21"         / C.Flag,
            "unk22"         / C.Flag,
            "unk23"         / C.Flag,
            "unk24"         / C.Flag,
            "OL"            / C.Flag,
            "unk26"         / C.Flag,
            "Hold"          / C.Flag,
                            
            "unk31"         / C.Flag,
            "unk32"         / C.Flag,
            "unk33"         / C.Flag,
            "unk34"         / C.Flag,
            "unk35"         / C.Flag,
            "err"           / C.Flag,
            "manrange"      / C.Flag,
            "rel"           / C.Flag,
                            
            "unk41"         / C.Flag,
            "unk42"         / C.Flag,
            "unk43"         / C.Flag,
            "unk44"         / C.Flag,
            "unk45"         / C.Flag,
            "unk46"         / C.Flag,
            "max"           / C.Flag,
            "min"           / C.Flag,

            "unk51"         / C.Flag,
            "unk52"         / C.Flag,
            "unk53"         / C.Flag,
            "unk54"         / C.Flag,
            "unk55"         / C.Flag,
            "unk56"         / C.Flag,
            "unk57"         / C.Flag,
            "unk58"         / C.Flag,

            "unk61"         / C.Flag,
            "unk62"         / C.Flag,
            "unk63"         / C.Flag,
            "unk64"         / C.Flag,
            "unk65"         / C.Flag,
            "unk66"         / C.Flag,
            "forward"       / C.Flag, # diode polarity: <-
            "reverse"       / C.Flag, # diode polarity: ->
            )


    def __init__(self, format="csv", full=False):
        self.iface = cp2110.CP2110Device()
        self.buf = bytearray()
        self.data = deque()
        self.ID = None  # instrument ID

        self.full = full    #
        # logging parameters
        self.interval = 0
        self.period = 0
        self.format = format
        
        self.package_no = 0
        self.first = True   # first logging package
        self.last_s = ""    # last status data
        self.__last_logtime = datetime.datetime.fromtimestamp(time.time()) 

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


    def streamreader(self, logging=True, period=None, interval=0):
        "Continuously read from data stream and process it"
        
        self.iface.purge_fifos()
        self.send_request("get_ID")
        self.send_request("confirm")
        self.interval = datetime.timedelta(seconds=interval)

        t0 = time.time()

        while True:
            t = time.time()
            self.buf.extend(self.iface.read(63))

            if len(self.buf) >= 26:
                # seek package signature
                while not self.buf.startswith(b"\xab\xcd"):
                    del(self.buf[0])
                    print("shift", file=sys.stderr)
                else:
                    dat = self.parsepackages()
                    if logging:
                        self.logger()
                if period and t-t0 >= period:
                    break


    def parsepackages(self):
        "parse stream buffer and return data as a dict"

        i = 0
        while len(self.buf) >= 26:
            package = self.package.parse(self.buf)
            rawpackage = self.package.build(package)
            checksum = sum(rawpackage[:-2])
            del(self.buf[:len(rawpackage)])
            i += 1

            if checksum != package["checksum"]:
                print("Warning: Checksum mismatch", file=sys.stderr)

            if package["payload"].startswith(b"\x02"): # data package
                mvals = self.mdata.parse(package["payload"])
                stat = self.stat.parse(mvals["stat"])
                dat = OrderedDict([
                    #("No",          self.package_no),
                    ("timestamp",   datetime.datetime.fromtimestamp(time.time())),
                    ("mode",        self.mode[mvals["mode"]]["name"]),
                    ("range",       self.mode[mvals["mode"]]["range"][int(mvals["range"])]),
                    ("value",       mvals["value"]),
                    ("unit",        self.mode[mvals["mode"]]["unit"][int(mvals["range"])]),
                    ("OL",          "OL" if stat["OL"] else ""),
                    ("hold",        "hold" if stat["Hold"] else ""),
                    ("rel",         "rel" if stat["rel"] else ""),
                    ("polarity",    "forward" if stat["forward"] else "reverse" if stat["reverse"] else ""),
                    ("manrange",    "manual" if stat["manrange"] else "auto"),
                    ("minmax",      "min" if stat["min"] else "max" if stat["max"] else ""),
                    ("err",         "Err" if stat["err"] else ""),
                    ("stat",        mvals["stat"]),
                ])
                if not self.full:
                    if dat["err"] == "Err" or dat["OL"] == "OL":
                        dat["value"] =""
                self.data.append(dat)
                self.package_no += 1
            elif package["payload"].startswith(b"\x00"): # device ID package
                self.ID = package["payload"][1:].decode("utf8")
            else:
                print(f"Warning: Unknown package type {hex(package['payload'][0])}. Skipping", file=sys.stderr)

        if i > 1 :
            print(f"Warning: parsed {i} packages from buffer => timestamps may be incorrect", file=sys.stderr)


    def logger(self):
        "print logging data"

        try:
            dat = self.data.popleft()
            if dat["timestamp"] - self.__last_logtime >= self.interval:
                self.__last_logtime = dat["timestamp"]
                if self.format == "csv":
                    del dat["stat"]
                    if self.first: 
                        print(",".join( [str(x) for x in dat.keys()] ))
                        self.first = False
                    print(",".join( [str(x) for x in dat.values()] ))
                elif self.format == "json":
                    del dat["stat"]
                    dat["timestamp"] = str(dat["timestamp"])
                    print(json.dumps(dat))
                elif self.format == "reversing":
                    s = " ".join([format(byte, "08b") for byte in dat["stat"]])
                    s_byte = "".join([format(byte, "02x") for byte in dat["stat"]])
                    if s != self.last_s:
                        print("     ", strcmp(self.last_s, s))
                        print("stat:", s, ":", s_byte)
                    self.last_s = s
                else:
                    sys.exit(f"unknown format '{self.format}'")
        except IndexError:
            pass




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass


