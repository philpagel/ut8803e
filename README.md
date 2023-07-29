# Talking to a UNI-T UT8803E bench multimeter 

This is an implementation of the data protocol used by the UNI-T UT8803E
(or UT8803) bench multimeter.


# Status 

Currently, only the model UT8803E/UT8803 is supported. 

The software has been tested successfully with a UT8803E on LINUX (Debian 12).
It does currently support all available button press commands and basic data logging and
some status information (`mode`, `OL`, `rel`, `hold` and `min/max`).
Other status information is still work in progress.

The UNI-T documentation suggests that, with some modifications, this *may* work
with other models, too:

* UT8802/UT8802N
* UT632/UT632N
* UT803/UT803N
* UT804/UT804N

Unfortunately, I do not have access to any of those models so I may be wrong.
If you have one of them and are willing to help, please get in touch.


# In a nutshell

Start logging data

    ./ut8803e.py log

Log to file
    
    ./ut8803e.py log > mydata.csv

Log for 30 seconds

    ./ut8803e.py -p 0:0:30 log

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

              d_val           transistor D value

              q_val           transistor Q value

              r_val           transistor resistance

              exit_dqr        exit DQR mode

    Options:
      -d, --debug        Turn on debugging information
      -p, --period TEXT  Length of logging period [HH:MM:SS]. Max period: 23:59:59
      --help             Show this message and exit.


Most commands act the exact same way as pressing the respective button
on the instrument. 

Logging data is printed in to `STDOUT` in `csv` format and can be redirected to
a file using the facilities of your operation system or shell.  E.g. `ut8803e/py
log > data.csv` on LINUX.

Debugging information is printed to `STDERR`.


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

