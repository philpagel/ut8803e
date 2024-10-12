# Protocol

To my knowledge, there is no official protocoll documentation published by the
manufacturer. So the protocol and data formats described below were reverse
engineered. By sniffing the communication between the instrument and the
original vendor software.

If you are interested in the revering process you can read about it in my
[blog](https://techbotch.org/blog/ut8803e-bench-meter/) (sorry, German only).

The instrument speaks USB-HID via the integrated CP2110 USB UART bridge.
Commands and data records are binary.


## Data logging

The instrument continuously streams measurement data at a rate of about 3
readings per second. This happens automatically – no specific polling command
is required.

## Commands

The following commands (given in hex) are supported and do exactly what the
corresponding press of a physical button would do:

    abcd04460001c2    # Hold
    abcd04470001c3    # Back light
    abcd04480001c4    # Select
    abcd04490001c5    # Manual Range
    abcd044a0001c6    # Auto Range
    abcd044b0001c7    # Min/Max
    abcd044c0001c8    # Exit Min/max
    abcd044d0001c9    # Rel
    abcd044e0001ca    # D Value
    abcd044f0001cb    # Q Value
    abcd04500001cc    # Exit DQR
    abcd04510001cd    # R value
    abcd04580001d4    # request device-ID

The original vendor software (Windows only) always sends some kind of
confirmation package after each command package (`abcd045a0001d6`). However, it
is unclear what this really does because all command packages I tested seem to
work fine without the extra package.





