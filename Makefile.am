#  pgp-pathfinder - Find a path from one PGP key to another
#  Copyright (C) 2001 Per Cederqvist
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. */

## Process this file with automake to produce Makefile.in

MYSQL = @MYSQL@
PYTHON = @PYTHON@

recreate_db: Makefile $(srcdir)/sqltypes.sed $(srcdir)/createdb.sql
	sed -f $(srcdir)/sqltypes.sed < $(srcdir)/createdb.sql \
		| $(MYSQL)
optimize_db: Makefile $(srcdir)/sqltypes.sed $(srcdir)/optimize.sql
	sed -f $(srcdir)/sqltypes.sed < $(srcdir)/optimize.sql \
		| $(MYSQL) pgppathfinder

backup:
	mysqldump -e -c -n -t pgppathfinder key_info key_uids key_sigs > $@.tmp
	mv $@.tmp $@.out

restore:
	$(MYSQL) pgppathfinder < backup.out
