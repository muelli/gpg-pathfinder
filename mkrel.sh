#!/bin/sh
#
#  This file is probably useful only to the maintainer of pru-backup.
#
#  Make a release.  See the file RELEASING for full instructions.
#  This file was created by Per Cederqvist and placed in the public
#  domain.
#

# Remove some files that we expect automake to create for us.
rm -f COPYING INSTALL mdate-sh missing
rm -f install-sh mkinstalldirs texinfo.tex

# Recreate all files.
./bootstrap.sh

# Set up a build environment.
./configure

# Make sure we have up-to-date dependencies.
make clean
make

# Finally, make the distribution.
make dist
