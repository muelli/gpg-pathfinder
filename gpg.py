# Simple gpg interaction

import os
import string

def run_gpg(args):
    cmd = "gpg "+string.join(args, " ")
    # print cmd
    p = os.popen(cmd)
    output = p.read()
    # print output
    return output

def decode_uid(s):
    s = unicode(s, 'utf-8')
    parts = s.split("\\")
    uid = parts[0]
    for p in parts[1:]:
        assert p[0] == 'x'
        uid += "%c%s" % (int(p[:2]), p[2:])
    # print "decode_uid(%s) -> %s" % (s, uid)
    return uid

class Key:
    def __init__(self, id, uid):
        self.id = id
        self.uid = uid

    def __repr__(self):
        return "<PGP key %X>" % self.id


def get_keys(id):
    data = run_gpg(["--with-colons", "--list-keys", id])
    data = data.split("\n")

    keys = []
    key = None

    for ln in data:
        if not ln:
            continue
        flds = ln.split(":")
        # print flds
        [typ, trust, length, alg, id, cre,
         exp, lid, otrust, uid, cls] = flds[:11]
        uid = decode_uid(uid)
        if typ == "pub":
            try:
                name = uid.encode("latin-1")
            except UnicodeError:
                name = "??"
            print "Public key for %s found" % name
            key = Key(long(id, 16), uid)
            keys.append(key)
        else:
            print "Unknown field %s" % typ

    return keys

def recv_key(id):
    run_gpg(["--recv-keys", id])

if __name__ == '__main__':
    print get_keys("EB144031")
