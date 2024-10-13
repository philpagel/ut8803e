# Talking to a UNI-T UT8803E bench multimeter 

This is an implementation of the data protocol used by the UNI-T UT8803E
(or UT8803) bench multimeter.


# Status 

The software provides all functionality of the original vendor software (but
without a GUI) plus a few things that are not available in the windows program.
However, there are still a few status flags that seem to exist but I haven't
figured out their meaning, yet.

It has been tested successfully with a UT8803E on LINUX (Debian 12).

I think it should also work on MacOS or Windows, but that is untested.  If you
have successfully tested it on those systems, please let me know and I'll update
this statement.

I no longer own the multimeter so if you find a bug I will need your help for
testing.


# In a nutshell

Start logging data

    ut8803e log

Log to file
    
    ut8803e log > mydata.csv

Log for 30 seconds in JSON format

    ut8803e -f json -p 0:0:30 log

Log for 1.5 hours

    ut8803e -p 1:30:00 log

Get device-ID

    ut8803e get_ID

Toggle `hold`

    ut8803e hold

Change display brightness 

    ut8803e brightness



# Installation

From the latest release file, download an installable file (`ut8803e*.tar.gz` or 
`ut8803e*.whl`) and install it with `pip` or `pipx`.


## Prerequisites

First, you need to install the `hidapi` library. On a Debian system it is provided by two
different libraries, so you can do:

    apt install libhidapi-hidraw0
    
or

    apt install libhidapi-libusb0


If you are on Windows, you need to download the zip file from the latest
release on the [hidapi repository](https://github.com/libusb/hidapi) on github
and the following permission discussion does not apply. For MacOS, I have no
clue. Please let me know if you do.

When plugging in the device, it will show up as `/dev/usbhidraw*`, be 
owned by root and not accessible to regular users:

    $ ls -la /dev/hid*
    crw------- 1 root root 241, 0 Okt 12 17:15 /dev/hidraw0

So running the program as a regular user will fail. For initial testing, you can
run as root:

    sudo ut8803e

But it is not recommended to do that for productive use. Instead, you need to install 
a `udev` rule file that makes the device user accessible. Create a file 
[`/etc/udev/rules.d/50-CP2110-hid.rules`](50-CP2110-hid.rules) and put this into it:

    # Make CP2110 usb hid devices user read/writeable
    KERNEL=="hidraw*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea80", MODE="0666“

Or just copy the file provided in this repository.

After re-plugging the multimeter, it should appear like this:

    $ ls -la /dev/hid*
    crw-rw-rw- 1 root root 241, 0 Okt 12 17:15 /dev/hidraw0

So now, regular users can read from and write to it.

## Install using `pipx` (recommended)

The recommended way of installing is `pipx`. If you don't already have that,
you need to install it, too:

    apt install pipx

Now, you can run
    
    pipx install ut8803e-*.tar.gz 

or
    
    pipx install ut8803e-*.whl 


## Install using `pip` and `venv` (more involved)

If you use `pip`, instead, you will most likely need to create a venv, first:

    python3 -m venv .venv
    source .venv/bin/activate
    python3 -m pip install ut8803e-*.tar.gz 

You will need to repeat the `source` part to activate the venv whenever you 
coma back and want to run the program.


# Usage

This is a simple command line tool that takes exactly on argument and supports a
few options:

    Usage: ut8803e [OPTIONS] CMD

      Commands:

          log             start logging data

          get_ID          get instrument id

          brightness      change display brightness (3 steps)

          select          press `select` button

          range_manual    switch to next manual range

          range_auto      set auto range

          minmax          set/toggle min/max mode

          exitminmax      exit min/max mode

          rel             set relative mode

          d_val           capacitor D value

          q_val           inductance Q value

          r_val           inductance/capacitor resistance

          exit_dqr        exit DQR mode

    Options:
      -p, --period TEXT       Length of logging period [HH:MM:SS]. Max period: 23:59:59
      -i, --interval INTEGER  Logging interval [s]
      -f, --format TEXT       Logging data format (csv/json/reversing)
      --full                  show value even if ERR or OL app

Most commands act the exact same way as pressing the respective button
on the instrument. 

Logging data is printed in to `STDOUT` in `csv` format, by default.  You can
also get JSON records with `--format json`. Finally, there is `--format
reversing` which will log binary and hex data of the status record. This is
intended for reverse engineering additional features or adding support for other
models.

and can be
redirected to a file using the facilities of your operation system or shell.
E.g. `ut8803e/py log > data.csv` on LINUX.

Warnings and Debugging information are printed to `STDERR`.


# Protocol reverse engineering

If you are interested in how I went about figuring out the communication
protocol, have a look at my [blog
post](https://techbotch.org/blog/ut8803e-bench-meter/index.html#ut8803e-bench-meter)
covering that. Sorry – only in German right now.

# Contributing

If you are interested to contribute, please open an issue that clearly
describes the change, feature or bugfix that you would like to suggest. Please do not
submit pull requests without discussing the issue first.

The UNI-T programming manual suggests that there are at least two more status flags that
haven't been implemented, yet and that I do not understand:

* Series/Parallel (SER/PAL) in capacity and inductance mode. There are
  corresponding indicators on the LCD but I have no idea what that means.
* Over/underflow – again not sure what exactly that is supposed to be.
  
So if you know anything about that – get in touch.

The UNI-T documentation suggests that, with some modifications, this *may* work
with other models, too:

* UT8802/UT8802N
* UT632/UT632N
* UT803/UT803N
* UT804/UT804N

Unfortunately, I do not have access to any of those models so I may be wrong.
If you have one of them and are willing to help, please get in touch.

