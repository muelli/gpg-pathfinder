import socket

import pgppathconfig
import pathdb

def fetched_key(keyfetcher):
    return long(keyfetcher.recv(10), 16)

def find_path(target, trusted, forbidden_keys = []):
    assert target > 0
    assert trusted > 0
    task = pathdb.create_task(target, trusted)
    keyfetcher = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    keyfetcher.connect(('localhost', pgppathconfig.keyfetcher_port))
    line = keyfetcher.recv(64)
    if line != "who-are-you\n":
        print "Bad heading from keyserver:", line
    keyfetcher.send("%d\n" % task)
    line = keyfetcher.recv(64)
    if line != "hello\n":
        print "Bad hello from keyserver:", line


    # Get the start- and endpoint.  We really, really need them.
    pending = []
    if pathdb.need_key(task, target, 0) == 0:
        pending.append(target)
    if target != trusted and pathdb.need_key(task, trusted, 0) == 0:
        pending.append(trusted)
    while len(pending) > 0:
        pending.remove(fetched_key(keyfetcher))

    pathdb.task_forbidden_keys(task, forbidden_keys)

    # Can we find a path without fetching a new key?
    target_dist = 0
    trust_dist = 0
    limit = 10
    trusted_extensible = 1
    pathdb.initial_setup(task, target, trusted)
    while target_dist < limit:
        path = pathdb.best_match_found(task, target_dist, trust_dist)
        if path != None:
            return path

        if trust_dist < target_dist and trust_dist < limit/2 \
           and trusted_extensible:
            new_entries = pathdb.extend_trust(task, trust_dist)
            if new_entries == 0:
                trusted_extensible = 0
            else:
                trust_dist += 1
                continue

        new_entries = pathdb.extend_target(task, target_dist)
        if new_entries == 0:
            break
        target_dist += 1

    # No path found in local database.  Fetch keys.
    pending_keys = pathdb.request_keys(task, limit)
    fetched_keys = 0
    while pending_keys > 0:
        print "Pending: %d Fetched: %d" % (pending_keys, fetched_keys),
        key_id = fetched_key(keyfetcher)
        fetched_keys += 1
        pending_keys -= 1
        print "Got 0x%08X" % key_id
        path, new_keys = pathdb.insert_sigs_of_key(task, key_id, limit)
        if path != None:
            return path
        pending_keys += new_keys

    return None


def print_path(path):
    if path == None:
        print "No match found"
    else:
        for k in path:
            print "0x%08X" % k,
        print

if __name__ == '__main__':
    pathdb.init()
    print "Starting"
    print_path(find_path(0x12345678L, 0x12345678L))
    print_path(find_path(0xF9036141L, 0xF9036141L))
    print_path(find_path(0x9AA2E311L, 0x94514BBDL))
    print_path(find_path(0x9AA2E311L, 0x57D395E1L))
    print "Ulla..."
    print_path(find_path(0xED2354B9L, 0x9AA2E311L))
    print "Horowitz..."
    print_path(find_path(0x1CF27FD5L, 0x9AA2E311L))
    print "Trojnara"
    print_path(find_path(0x74C732D1L, 0x9AA2E311L, [
    	0xFB5E1519L, 0x4413B691L]))
    print_path(find_path(0x20B19259L, 0xD294608EL, []))
    print "Done"
