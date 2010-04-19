#!/bin/sh
# $Revision: 1.3 $
# $Date: 2007-03-01 21:41:46 $
# Ilya Cassina < icassina@gmail.com >
#
# DESCRIPTION:
# USAGE:
# LICENSE: ___

sudo rm -rf /usr/lib/python2.6/site-packages/{pymt,PyMT*}

sudo python setup.py install
