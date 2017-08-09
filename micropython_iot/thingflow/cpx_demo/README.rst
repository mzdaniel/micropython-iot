=========================================
MTQQ CircuitPlayground Express (CPX) demo
=========================================
This directory contains example code to drive a CircuitPlayground Express neopixel ring with wireless data.

The setup involves a ESP8266 that captures an analog signal from a potentiometer and transmits it wirelessly using an MQTTWriter. Then the host
computer decodes the wireless MQTTReader data and bridges it to the CPX to lit
the neopixel ring. One interesting aspect of this setup, is that CPX runs a
derivative version of micropython too and the host drives the CPX using its
REPL. This way the host can technically talk to the full array of sensors and transducers without being artificially limited by APIs.

Files in this directory
=======================

* ``cpx_driver.py`` - Implement REPL bridge, exposing the light sensor and the
  neopixel ring drivers
* ``docs/_build`` - Sphinx creates and puts its output in this subdirectory. A
  ``make clean`` in ``docs/`` will delete this directory and its contents.
* ``docs/conf.py`` - configuration file for Sphinx
* ``make_zip.sh`` - to build a zipfile with class content software and docs
* ``example_code/`` - subdirectory with Python example code
* ``lecture.pptx`` - overview presentation to give at the start of the class.
* ``lecture.pdf`` - pdf version of the overview presentation
