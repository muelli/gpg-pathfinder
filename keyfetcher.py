import string
import select
import socket

import pgppathconfig
import pathdb
import hkp

def toploop(listenfd):
    sessions = {}
    timeout = 60
    while 1:
        # Look for new and dead clients.
        r = [listenfd] + map(lambda(x): x.fileno(), sessions.values())
        r, w, e = select.select(r, [], [], timeout)
        if listenfd in r:
            # New client.
            timeout = 0
            client = listenfd.accept()[0]
            client.send("who-are-you\n")
            task = int(string.strip(client.recv(64)))
            client.send("hello\n")
            pathdb.activate_task(task)
            sessions[task] = client
        if len(sessions) == 0:
            timeout = 60
            continue

        for task in sessions.keys():
            if sessions[task].fileno() in r:
                # Dead client.
                pathdb.deactivate_task(task)
                sessions[task].close()
                del sessions[task]

        # Look for real work.
        (key_id, task) = pathdb.key_to_fetch()
        if key_id == None:
            if timeout == 0:
                timeout = 0.05
            else:
                timeout *= 2
                if timeout > 30:
                    timeout = 30
            continue
        assert key_id != 0
        timeout = 0
        key_data = hkp.get_key(key_id)
        # If we find no match, insert an entry to show that we tried.
        if len(key_data) == 0:
            print "0x%08X: fetch failed" % key_id
            key_data.append(hkp.key_info(key_id, None))
        tasks = {}
        for k in key_data:
            print "0x%08X: retrieved" % key_id
            for t in pathdb.insert_key_update_tasks(k, task):
                tasks[t] = None
        for t in tasks.keys():
            if sessions.has_key(t):
                sessions[t].send("0x%08X" % key_id)
        
    

def start():
    listenfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listenfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listenfd.bind(('localhost', pgppathconfig.keyfetcher_port))
    listenfd.listen(3)
    pathdb.init()
    pathdb.deactivate_all_tasks()
    toploop(listenfd)

if __name__ == '__main__':
    start()
