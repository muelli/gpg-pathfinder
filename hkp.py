import htmlentitydefs
import urllib2
import re

import gpgpathconfig

matcher = re.compile('('
                     '(?P<type>pub|uid|sig)'
                     ' *'
                     '((?P<bits>\\d+)'
                     '(?P<keytype>[A-Za-z]?)'
                     '/)?'
                     '<[^>]+>'
                     '(?P<key>[0-9A-F]{8,8})'
                     '</a> *'
                     '((?P<year>\\d{4,4})/'
                     '(?P<month>\\d{2,2})/'
                     '(?P<day>\\d{2,2}))? '
                     '| {30,30})'
                     '(?P<name>.*)'
                     )

tag_remover = re.compile('<[^>]*>')
entities = re.compile('&([^;]*);')

def decode_entity(m):
    s = m.group(1)
    if s == '':
        return ''
    if s[0] == '#':
        res = atoi(s[1:])
        if 0 < res < 0x100:
            return chr(res)
        
    res = htmlentitydefs.entitydefs.get(s)
    if res != None:
        return res

    return '.'

def decode_name(name):
    # Remove all tags.
    name = ''.join(tag_remover.split(name))
    # Transform html entities.
    name = entities.sub(decode_entity, name)
    return name


class key_info:
    def __init__(self, key_id, creation_date):
        self.__key_id = key_id
        self.__creation_date = creation_date
        self.__names = []
        self.__signers = []

    def add_uid(self, name):
        self.__names.append(name)

    def add_sig(self, signer):
        if signer not in self.__signers:
            self.__signers.append(signer)

    def key_id(self):
        return self.__key_id

    def creation_date(self):
        return self.__creation_date

    def names(self):
        return self.__names

    def signed_by(self):
        return self.__signers


def get_key(key_id):
    f = None
    for i in range(5):
        try:
            f = urllib2.urlopen('http://%s:11371/pks/lookup?op=vindex&'
                                'search=0x%08X' %
                                (gpgpathconfig.keyserver, key_id))
            break
        except urllib2.URLError:
            print "FAIL: retrying..."

    if f == None:
        print "FAILed to fetch 0x%08X" % key_id
        return []
    keys = []

    for line in f.readlines():
        if len(line) > 0 and line[-1] == '\n':
            line = line[:-1]
        if len(line) > 0 and line[-1] == '\r':
            line = line[:-1]
        m = matcher.match(line)
        if m != None:
            d = m.groupdict()
            if d['type'] == 'pub':
                keys.append(key_info(long(d['key'], 16),
                                     d['year'] + d['month'] + d['day']))
                keys[-1].add_uid(decode_name(d['name']))
            elif d['type'] == 'sig':
                keys[-1].add_sig(long(d['key'], 16))
            elif d['type'] == 'uid' or d['type'] == None:
                keys[-1].add_uid(decode_name(d['name']))
            else:
                print "BAD MATCH:", line
    f.close()

    return keys

if __name__ == '__main__':
    def use_info(foo):
        for k in foo:
            print "0x%08X %s" % (k.key_id(), k.creation_date())
            for n in k.names():
                print n
            for i in k.signed_by():
                print "0x%08X" % i,
            print
            print "-" * 70
            pathdb.insert_key(k)

    import pathdb
    pathdb.init()

    use_info(get_key(0xD294608E))
    use_info(get_key(0x6A9591D0))
    use_info(get_key(0x001B3BA1))
