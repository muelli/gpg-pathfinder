import socket

import pgppathconfig
import pathdb

def find_path(target, trusted):
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
        pending.remove(long(keyfetcher.recv(64), 16))

    target_dist = 0
    trusted_dist = 0
    pathdb.initial_setup(task, target, trusted)
    while 1:
        path = pathdb.best_match_found(task, target_dist, trusted_dist)
        if path != None:
            return path
        new_entries = pathdb.extend_target(task, target_dist)
        if new_entries == 0:
            return None
        target_dist += 1


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
    print "Done"
