import MySQLdb

_DB = None

def init():
    global _DB
    _DB = MySQLdb.connect(db='pgppathfinder')

def _insert_key(cursor, k):
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

def insert_key(k):
    cursor = _DB.cursor()
    _insert_key(cursor, k)
    cursor.close()
    _DB.commit()

def insert_key_update_tasks(k, task):
    cursor = _DB.cursor()
    cursor.execute('lock tables keys_needed write, key_info write,'
                   ' key_uids write, key_sigs write')
    _insert_key(cursor, k)
    cursor.execute('select taskno from keys_needed where key_id = %s',
                   (k.key_id(), ))
    tasks = cursor.fetchall()
    cursor.execute('delete from keys_needed where key_id = %s',
                   (k.key_id(), ))
    cursor.execute('unlock tables')
    cursor.execute('select max(schedule) from tasks')
    schedule = cursor.fetchone()[0]
    cursor.execute('update tasks set fetched = fetched + 1, schedule = %s'
                   ' where taskno = %s',
                   (task, schedule + 1))
    cursor.close()
    _DB.commit()
    return map(lambda(row): row[0], tasks)

def activate_task(task):
    cursor = _DB.cursor()
    cursor.execute('update tasks set active = 1 where taskno = %s', task)
    cursor.close()
    _DB.commit()

def deactivate_task(task):
    cursor = _DB.cursor()
    cursor.execute('update tasks set active = 0 where taskno = %s', task)
    cursor.close()
    _DB.commit()

def deactivate_all_tasks():
    cursor = _DB.cursor()
    cursor.execute('update tasks set active = 0')
    cursor.close()
    _DB.commit()

def key_to_fetch():
    """Find the next key to fetch from a PGP keyserver.

    Returns a tuple containing the key id and the task, or
    (None, None) if there is nothing to do.
    """

    cursor = _DB.cursor()
    cursor.execute('select k.key_id, k.taskno'
                   ' from keys_needed k, tasks t'
                   ' where k.taskno = t.taskno'
                   ' and t.active = 1'
                   ' order by t.schedule, k.distance'
                   ' limit 1')
    row = cursor.fetchone()
    cursor.close()
    _DB.commit()
    if row == None:
        return (None, None)
    else:
        return (row[0], row[1])

def create_task(target, trusted):
    cursor = _DB.cursor()
    cursor.execute('insert into tasks'
                   ' (target, trusted, fetched, created, active, schedule)'
                   ' values'
                   ' (%s, %s, 0, NOW(), 0, 0)',
                   (target, trusted))
    cursor.execute('select last_insert_id()')
    task = cursor.fetchone()[0]
    cursor.close()
    _DB.commit()
    return task

def need_key(task, key_id, distance):
    cursor = _DB.cursor()
    cursor.execute('lock tables keys_needed write, key_info read')
    cursor.execute('select count(*) from key_info where key_id = %s',
                   (key_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute('insert into keys_needed (taskno, key_id, distance)'
                       ' values (%s, %s, %s)',
                       (task, key_id, distance))
    cursor.execute('unlock tables')
    _DB.commit()
    return count
