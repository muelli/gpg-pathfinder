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
#
# We don't care about which uid a signator signed.  If he has signed
# any uid, the signature is good for all of them, as far as we are
# concerned.

create table key_info (
	key_id		uint32		not null,

	# We store NULL in the fields below if we know for sure that
	# the key servers don't know anything about this key.

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
						  # we know nothing about yet.

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
	finished	datetime	null,
	lastused	datetime	null,
	pathfound	bool		null,
	active		bool		not null,
	schedule	uint64		not null,

	INDEX(taskno),
	INDEX(target, trusted),
	INDEX(active),
	INDEX(schedule)
);

create table task_trusted (
	taskno		uint64		not null,
	key_id		uint64		not null,
	signed_by	uint64		not null,
	distance	uint8		not null,

	INDEX(taskno),
	INDEX(key_id),
	INDEX(signed_by)
);

create table task_target (
	taskno		uint64		not null,
	key_id		uint64		not null,
	signed_by	uint64		not null,
	distance	uint8		not null,

	INDEX(taskno),
	INDEX(key_id),
	INDEX(signed_by)
);

create table keys_needed (
	taskno		uint64		not null,
	key_id		uint64		not null,
	distance	uint8		not null,

	INDEX(taskno, distance)
);
