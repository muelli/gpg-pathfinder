import MySQLdb

_DB = None

type_conv = { MySQLdb.FIELD_TYPE.TINY: int,
              MySQLdb.FIELD_TYPE.SHORT: int,
              MySQLdb.FIELD_TYPE.LONG: long,
              MySQLdb.FIELD_TYPE.FLOAT: float,
              MySQLdb.FIELD_TYPE.DOUBLE: float,
              MySQLdb.FIELD_TYPE.LONGLONG: long,
              MySQLdb.FIELD_TYPE.INT24: int,
              MySQLdb.FIELD_TYPE.YEAR: int }
def init():
    global _DB
    _DB = MySQLdb.connect(db='pgppathfinder', conv=type_conv)

def _insert_key(cursor, k):
    cursor.execute('delete from key_info where key_id = %s', (k.key_id(),))
    cursor.execute('delete from key_uids where key_id = %s', (k.key_id(),))
    cursor.execute('delete from key_sigs where key_id = %s', (k.key_id(),))
    cursor.execute('insert into key_info (key_id, creation_date, sigs_updated)'
                   ' values (%s, %s, NOW())',
                   (k.key_id(), k.creation_date()))

    if len(k.names()) > 0:
        cursor.executemany('insert into key_uids (key_id, name)'
                           ' values (%s, %s)',
                           zip([k.key_id()] * len(k.names()),
                               k.names()))
    if len(k.signed_by()) > 0:
        cursor.executemany('insert into key_sigs (key_id, signed_by) '
                           ' values (%s, %s)',
                           zip([k.key_id()] * len(k.signed_by()),
                               k.signed_by()))

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
                   (schedule + 1, task))
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
    """Enqueue a request for a key.
    Returns true if the key is already present.
    Inserts a request for the key and returns false if the key is missing.
    """

    assert key_id > 0
    cursor = _DB.cursor()
    cursor.execute('lock tables keys_needed write, key_info read')
    cursor.execute('select count(*) from key_info where key_id = %s',
                   (key_id, ))
    count = cursor.fetchone()[0]
    if count == 0:
        # print "Inserting needed key 0x%08X task=%d dist=%d" % (
        #     key_id, task, distance)
        cursor.execute('insert into keys_needed (taskno, key_id, distance)'
                       ' values (%s, %s, %s)',
                       (task, key_id, distance))
    cursor.execute('unlock tables')
    cursor.close()
    _DB.commit()
    return count

def initial_setup(taskno, target, trusted):
    cursor = _DB.cursor()
    cursor.execute('insert into task_target'
                   ' (taskno, key_id, signed_by, distance)'
                   ' values (%s, 0, %s, 0)',
                   (taskno, target))
    cursor.execute('insert into task_trusted'
                   ' (taskno, key_id, signed_by, distance)'
                   ' values (%s, %s, 0, 0)',
                   (taskno, trusted))
    cursor.close()
    _DB.commit()

def best_match_found(taskno, target_dist, trust_dist):
    cursor = _DB.cursor()
    cursor.execute('select target.key_id, target.signed_by, trusted.signed_by'
                   ' from task_target target, task_trusted trusted'
                   ' where target.signed_by = trusted.key_id'
                   ' and target.taskno = %s'
                   ' and trusted.taskno = %s'
                   ' and target.distance = %s'
                   ' and trusted.distance = %s'
                   ' order by target.distance+trusted.distance'
                   ' limit 1',
                   (taskno, taskno, target_dist, trust_dist))
    row = cursor.fetchone()
    cursor.close()
    _DB.commit()
    if row == None:
        result = None
    else:
        return backtrack(taskno, row[0], target_dist,
                         row[1], row[2], trust_dist)

def backtrack(taskno, best_target, target_dist,
              middle, best_trust, trust_dist):
    # We have found a match!  Now, backtrack.

    result = [best_target, middle, best_trust]

    # print "Match found.  Middle: 0x%08X 0x%08X 0x%08X" % tuple(result)

    if target_dist == 0:
        assert best_target == 0
        del result[0]
        best_target = middle
        # print "(left removed)"
    if trust_dist == 0:
        assert best_trust == 0
        del result[-1]
        best_trust = middle
        # print "(right removed)"

    cursor = _DB.cursor()

    while target_dist > 1:
        cursor.execute('select key_id from task_target'
                       ' where signed_by = %s and distance = %s'
                       ' and taskno = %s'
                       ' limit 1',
                       (best_target, target_dist - 1, taskno))
        row = cursor.fetchone()
        assert row != None
        best_target = row[0]
        result.insert(0, best_target)
        target_dist -= 1
        # print "(left added: 0x%08X)" % best_target

    while trust_dist > 1:
        cursor.execute('select signed_by from task_trusted'
                       ' where key_id = %s and distance = %s'
                       ' and taskno = %s'
                       ' limit 1',
                       (best_trust, trust_dist - 1, taskno))
        row = cursor.fetchone()
        assert row != None
        best_trust = row[0]
        result.append(best_trust)
        trust_dist -= 1
        # print "(right added: 0x%08X)" % best_trust
    cursor.close()
    _DB.commit()
    return result

def extend_target(task, target_dist):
    reader = _DB.cursor()
    sel = _DB.cursor()
    ins = _DB.cursor()
    count = 0
    # print "Extending", task, "old distance", target_dist
    reader.execute('select sig.key_id, sig.signed_by'
                   ' from key_sigs sig, task_target target'
                   ' where sig.key_id = target.signed_by'
                   ' and target.taskno = %s'
                   ' and target.distance = %s',
                   (task, target_dist))
    target_dist += 1
    while 1:
        row = reader.fetchone()
        if row == None:
            break
        sel.execute('select count(*) from task_target'
                    ' where signed_by = %s and taskno = %s',
                    (row[1], task))
        sel_row = sel.fetchone()
        if sel_row[0] > 0:
            # print "Extending With 0x%08X 0x%08X -- not!" % (row[0], row[1])
            continue
        sel.execute('select count(*) from task_forbidden'
                    ' where key_id = %s and taskno = %s',
                    (row[1], task))
        sel_row = sel.fetchone()
        if sel_row[0] > 0:
            # print "Extending With 0x%08X 0x%08X -- bad!" % (row[0], row[1])
            continue
        count += 1
        # print "Extending With 0x%08X 0x%08X" % (row[0], row[1])
        ins.execute('insert into task_target'
                    ' (taskno, key_id, signed_by, distance)'
                    ' values'
                    ' (%s, %s, %s, %s)',
                    (task, row[0], row[1], target_dist))
    # print "Extending... done."
    reader.close()
    sel.close()
    ins.close()
    _DB.commit()
    return count


def extend_trust(task, trust_dist):
    reader = _DB.cursor()
    sel = _DB.cursor()
    ins = _DB.cursor()
    count = 0
    # print "Ext trust", task, "old distance", trust_dist
    reader.execute('select sig.key_id, sig.signed_by'
                   ' from key_sigs sig, task_trusted trust'
                   ' where sig.signed_by = trust.key_id'
                   ' and trust.taskno = %s'
                   ' and trust.distance = %s',
                   (task, trust_dist))
    trust_dist += 1
    while 1:
        row = reader.fetchone()
        if row == None:
            break
        sel.execute('select count(*) from task_trusted'
                    ' where key_id = %s and taskno = %s',
                    (row[0], task))
        sel_row = sel.fetchone()
        if sel_row[0] > 0:
            # print "Ext trust with 0x%08X 0x%08X -- not!" % (row[0], row[1])
            continue
        sel.execute('select count(*) from task_forbidden'
                    ' where key_id = %s and taskno = %s',
                    (row[0], task))
        sel_row = sel.fetchone()
        if sel_row[0] > 0:
            # print "Ext trust with 0x%08X 0x%08X -- bad!" % (row[0], row[1])
            continue

        count += 1
        # print "Ext trust with 0x%08X 0x%08X" % (row[0], row[1])
        ins.execute('insert into task_trusted'
                    ' (taskno, key_id, signed_by, distance)'
                    ' values'
                    ' (%s, %s, %s, %s)',
                    (task, row[0], row[1], trust_dist))
    # print "Ext trust... done."
    reader.close()
    sel.close()
    ins.close()
    _DB.commit()
    return count

def request_keys(task, distance_limit):
    cursor = _DB.cursor()
    cursor.execute('lock tables keys_needed write,'
                   ' key_info read, task_target read')
    # print "Requesting..."
    cursor.execute('select %s, task_target.signed_by, task_target.distance + 1'
                   ' from task_target'
                   ' left join key_info'
                   ' on task_target.signed_by = key_info.key_id'
                   ' where key_info.key_id is null'
                   ' and task_target.taskno = %s'
                   ' and task_target.distance < %s',
                   (task, task, distance_limit - 1))
    rows = cursor.fetchall()
    if len(rows) > 0:
        # print "Found:", len(rows)
        cursor.executemany('insert into keys_needed (taskno, key_id, distance)'
                           ' values (%s, %s, %s)',
                           rows)
    else:
        # print "None found"
        pass
    cursor.execute('unlock tables')
    cursor.close()
    _DB.commit()
    return len(rows)

def insert_sigs_of_key(task, key_id, limit):
    reader = _DB.cursor()
    ins = _DB.cursor()
    sel = _DB.cursor()

    # Insert signatures into task_target.
    reader.execute('select t.taskno, s.key_id, s.signed_by, t.distance + 1'
                   ' from key_sigs s, task_target t'
                   ' where s.key_id = t.signed_by'
                   ' and t.taskno = %s'
                   ' and s.key_id = %s'
                   ' and t.distance < %s',
                   (task, key_id, limit))
    new_requests = 0
    any_inserted = 0
    while 1:
        row = reader.fetchone()
        if row == None:
            break
        sel.execute('select count(*) from task_target'
                    ' where signed_by = %s'
                    ' and taskno = %s'
                    ' and distance <= %s',
                    (row[2], task, row[3] - 1))
        sel_row = sel.fetchone()
        if sel_row[0] > 0:
            # print "Extending With 0x%08X 0x%08X -- not!" % (row[1], row[2])
            continue
        sel.execute('select count(*) from task_forbidden'
                    ' where key_id = %s and taskno = %s',
                    (row[2], task))
        sel_row = sel.fetchone()
        if sel_row[0] > 0:
            # print "Extending With 0x%08X 0x%08X -- bad!" % (row[1], row[2])
            continue
        any_inserted = 1
        # print "Extending With 0x%08X 0x%08X" % (row[1], row[2])
        ins.execute('insert into task_target'
                    ' (taskno, key_id, signed_by, distance)'
                    ' values'
                    ' (%s, %s, %s, %s)',
                    row)
        if row[3] < limit:
            if need_key(task, row[2], row[3]):
                print "Scheduling check of 0x%08X" % key_id
                ins.execute('insert into task_unchecked'
                            ' (taskno, key_id, distance)'
                            ' values'
                            ' (%s, %s, %s)',
                            (task, row[2], row[3]))
            else:
                new_requests += 1

    if any_inserted:
        # Check for new overlap.
        sel.execute('select target.key_id, target.signed_by,'
                    ' trusted.signed_by,'
                    ' target.distance, trusted.distance'
                    ' from task_target target, task_trusted trusted'
                    ' where target.signed_by = trusted.key_id'
                    ' and target.taskno = %s'
                    ' and trusted.taskno = %s'
                    ' and trusted.key_id = %s'
                    ' order by target.distance+trusted.distance'
                    ' limit 1',
                   (task, task, key_id))
        row = sel.fetchone()
        if row != None:
            reader.close()
            sel.close()
            ins.close()
            _DB.commit()
            return (backtrack(task, row[0], row[3], row[1], row[2], row[4]),
                    new_requests)

    # FIXME:Insert signatures into task_trusted, similarly to the above code.
    # FIXME:...and then check for new overlap, again.

    # print "Deleting from task_uncheckd(%d, 0x%08X)" % (task, key_id)
    ins.execute('delete from task_unchecked'
                ' where taskno = %s'
                ' and key_id = %s',
                (task, key_id))
    ins.close()
    sel.close()
    reader.close()
    _DB.commit()

    return (None, new_requests)

def task_forbidden_keys(task, forbidden_keys):
    # print "FORBIDDING", task, forbidden_keys
    if len(forbidden_keys) > 0:
        cursor = _DB.cursor()
        cursor.executemany('insert into task_forbidden (taskno, key_id)'
                           ' values (' + str(task) + ', %s)',
                           zip(forbidden_keys))
        cursor.close()
        _DB.commit()

def unchecked_key(task):
    sel = _DB.cursor()
    sel.execute('select key_id from task_unchecked'
                ' where taskno = %s'
                ' order by distance'
                ' limit 1',
                (task, ))
    res = sel.fetchone()
    if res == None:
        return None
    else:
        return res[0]
