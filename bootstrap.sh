#!/bin/sh
#
#  This file is probably useful only to the maintainer.
#  Create "configure" and all the files it needs.
#  This file was created by Per Cederqvist and placed in the public domain.

aclocal
autoconf
# autoheader
automake -a
