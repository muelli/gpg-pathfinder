import socket

import pgppathconfig
import pathdb

def findpath(target, trusted):
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

    # FIXME: the rest of this functions is just demo code.
    if pathdb.need_key(task, target, 1) == 0:
        key = keyfetcher.recv(64)
        if long(key, 16) != target:
            print "Bad key info", key
        else:
            print "Target fetched OK"
    else:
        print "Target already present in database"


if __name__ == '__main__':
    pathdb.init()
    findpath(0x12345678, 0x12345678)
