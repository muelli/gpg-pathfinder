# Start from scratch.

drop database if exists pgppathfinder;
create database pgppathfinder;
use pgppathfinder;

# Persistent information about a key.  When anything is inserted into
# key_info, the key_uids and key_sigs tables are also updated for the
# same key.
#
# We use the 32-bit key ID, even though it is not guaranteed to be
# unique.  This may cause us to report false paths.  Big deal.  The
# end user *must* check the signatures to get any security, and the
# false path will be detected than.
create table key_info (
	# Info about a key.
	key_id		uint32		not null,

	# We store NULL in the fields below if we know for sure that
	# the key servers don't know anything about this key.
	key_type	char(8)		null, # "1024R"
	creation_date	date		null,

	# When was the above info, and corresponding info in key_sigs
	# and key_uids, last checked with a key server?
	sigs_updated	datetime	not null,

	INDEX(key_id)
);

create table key_uids (
	key_id		uint32		not null,
	name		varchar(255),

	INDEX(key_id)
);

create table key_sigs (
	key_id		uint32		not null,
	signed_by	uint32		not null, # May refer to a key
						  # we know nothing about.

	INDEX(key_id),
	INDEX(signed_by)
);

# Our work queue.
create table tasks (
	taskno		uint64 		auto_increment not null,
	target		uint64		not null,
	trusted		uint64		not null,
	fetched		uint32		not null,
	created		datetime	not null,

	INDEX(taskno)
);
