import MySQLdb

_DB = None

def init():
    global _DB
    _DB = MySQLdb.connect(db='pgppathfinder')

def insert_key(k):
    cursor = _DB.cursor()
    cursor.execute('delete from key_info where key_id = %s', (k.key_id(),))
    cursor.execute('delete from key_uids where key_id = %s', (k.key_id(),))
    cursor.execute('delete from key_sigs where key_id = %s', (k.key_id(),))
    cursor.execute('insert into key_info (key_id, creation_date, sigs_updated)'
                   ' values (%s, %s, NOW())',
                   (k.key_id(), k.creation_date()))
    
    cursor.executemany('insert into key_uids (key_id, name) values (%s, %s)',
                       zip([k.key_id()] * len(k.names()), k.names()))
    cursor.executemany('insert into key_sigs (key_id, signed_by) '
                       ' values (%s, %s)',
                       zip([k.key_id()] * len(k.signed_by()), k.signed_by()))
    _DB.commit()
