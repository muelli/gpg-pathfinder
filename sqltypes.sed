s/[ 	][ 	]*/ /g
s/bool/tinyint unsigned/g
s/uint8/tinyint unsigned/g
s/uint16/smallint unsigned/g
s/uint24/mediumint unsigned/g
s/uint32/integer unsigned/g
s/uint64/bigint unsigned/g
s/int8/tinyint/g
s/int16/smallint/g
s/int24/mediumint/g
s/int32/integer/g
s/int64/bigint/g
s/#.*//g
