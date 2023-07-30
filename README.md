# Talking to a UNI-T UT8803E bench multimeter 

This is an implementation of the data protocol used by the UNI-T UT8803E
(or UT8803) bench multimeter.


# Status 

The software provides all functionality of the original vendor software (but
without a GUI) plus a few things that are not available in the windows
program. However, it is not feature complete, yet: There are still a few status
flags that seem to exist but I haven't figured out their meaning, yet.

It has been tested successfully with a UT8803E on LINUX (Debian 12).


# In a nutshell

Start logging data

    ./ut8803e.py log

Log to file
    
    ./ut8803e.py log > mydata.csv

Log for 30 seconds in JSON format

    ./ut8803e.py -f json -p 0:0:30 log

Log for 1.5 hours

    ./ut8803e.py -p 1:30:00 log

Get device-ID

    ./ut8803e.py get_ID

Toggle `hold`

    ./ut8803e.py hold

Change display brightness 

    ./ut8803e.py brightness



# Requirements

This program depends on a few Python libraries:

* [pycp2110](https://github.com/rginda/pycp2110)
* [construct](https://github.com/construct/construct)
* [click](https://click.palletsprojects.com)

You can install them like this:

    pip3 install -r requirements.txt

`pycp2110` depends on [pyhidapi](https://github.com/apmorton/pyhidapi) (will be
installed automatically) which in turn requires the `hidapi` library. You need
to install that yourself according to the instructions in the link above.

For Debian, this is the way to do it:

    apt install libhidapi-hidraw0
    
    # or

    apt install libhidapi-libusb0


# Usage

This is a simple command line tool that takes exactly on argument and supports a
few options:

    Usage: ut8803e.py [OPTIONS] CMD

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
      -p, --period TEXT  Length of logging period [HH:MM:SS]. Max period: 23:59:59
      -f, --format TEXT  Logging data format (csv/json/reversing)
      --full             show value even if ERR or OL app

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
describes the change, feature or bugfix that you would like to suggest.  If you
want to implement or fix something yourself, you can submit a pull-request that
addresses your issue. It makes sense to first discuss the issue before you get
to work with coding. Please open a new branch for your pull request – do not
use `main`.

The UNI-T programming manual suggests that there are at least two more status flags that
haven't been implemented, yet and that I do not understand:

* Series/Parallel (SER/PAL/) in capacity and inductance mode. There are
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

