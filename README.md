# Talking to a UNI-T UT8803E bench multimeter 

This is an implementation of the data protocol used by the UNI-T UT8803E
(or UT8803) bench multimeter.


# Status 

Currently, only the model UT8803E/UT8803 is supported. 

The software has been tested successfully with a UT8803E on LINUX (Debian 12).

The UNI-T documentation suggests that this *may* work with other models, too:

* UT8802\UT8802N
* UT632\UT632N
* UT803\UT803N
* UT804\UT804N

That will most likely require some modifications of the data parser.
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

    /ut8803e.py get_ID

Toggle `hold`

    ./ut8803e.py hold

Change display brightness 

    ./ut8803e.py brightness



# Requirements

This program depends on a few Python libraries:

* pycp2110
* construct
* click

You can install them like this:

    pip3 install -r requirements.txt

In addition, you need to make sure that `libhidapi-hidraw0` is installed on
your system.

    sudo apt install libhidapi-hidraw0

caution: if the `hid` package is installed, the script will fail. So either
make sure to `pip3 uninstall hid`, or have it running in a venv.

XXX – is that still true?


# Contributing

If you are interested to contribute, please open an issue that clearly
describes the change, feature or bugfix that you would like to suggest.  If you
want to implement or fix something yourself, you can submit a pull-request that
addresses your issue. It makes sense to first discuss the issue before you get
to work with coding. Please open a new branch for your pull request – do not
use `main`.

