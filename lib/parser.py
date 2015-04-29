#!/usr/bin/env python
#
# https://github.com/git/git/blob/master/Documentation/technical/index-format.txt
#

import binascii
import collections
import mmap
import struct
import sys


def check(boolean, message):
    if not boolean:
        import sys
        print "error: " + message
        sys.exit(1)


def parse(filename, pretty=True):
    with open(filename, "rb") as o:
        f = mmap.mmap(o.fileno(), 0, access=mmap.ACCESS_READ)

        def read(format):
            # "All binary numbers are in network byte order."
            # Hence "!" = network order, big endian
            format = "! " + format
            bytes = f.read(struct.calcsize(format))
            return struct.unpack(format, bytes)[0]

        index = collections.OrderedDict()

        # 4-byte signature, b"DIRC"
        index["signature"] = f.read(4).decode("ascii")
        check(index["signature"] == "DIRC", "Not a Git index file")

        # 4-byte version number
        index["version"] = read("I")
        check(index["version"] in {2, 3},
            "Unsupported version: %s" % index["version"])

        # 32-bit number of index entries, i.e. 4-byte
        index["entries"] = read("I")

        yield index

        for n in range(index["entries"]):
            entry = collections.OrderedDict()

            entry["entry"] = n + 1

            entry["ctime_seconds"] = read("I")
            entry["ctime_nanoseconds"] = read("I")
            if pretty:
                entry["ctime"] = entry["ctime_seconds"]
                entry["ctime"] += entry["ctime_nanoseconds"] / 1000000000
                del entry["ctime_seconds"]
                del entry["ctime_nanoseconds"]

            entry["mtime_seconds"] = read("I")
            entry["mtime_nanoseconds"] = read("I")
            if pretty:
                entry["mtime"] = entry["mtime_seconds"]
                entry["mtime"] += entry["mtime_nanoseconds"] / 1000000000
                del entry["mtime_seconds"]
                del entry["mtime_nanoseconds"]

            entry["dev"] = read("I")
            entry["ino"] = read("I")

            # 4-bit object type, 3-bit unused, 9-bit unix permission
            entry["mode"] = read("I")
            if pretty:
                entry["mode"] = "%06o" % entry["mode"]

            entry["uid"] = read("I")
            entry["gid"] = read("I")
            entry["size"] = read("I")

            entry["sha1"] = binascii.hexlify(f.read(20)).decode("ascii")
            entry["flags"] = read("H")

            # 1-bit assume-valid
            entry["assume-valid"] = bool(entry["flags"] & (0b10000000 << 8))
            # 1-bit extended, must be 0 in version 2
            entry["extended"] = bool(entry["flags"] & (0b01000000 << 8))
            # 2-bit stage (?)
            stage_one = bool(entry["flags"] & (0b00100000 << 8))
            stage_two = bool(entry["flags"] & (0b00010000 << 8))
            entry["stage"] = stage_one, stage_two
            # 12-bit name length, if the length is less than 0xFFF (else, 0xFFF)
            namelen = entry["flags"] & 0xFFF

            # 62 bytes so far
            entrylen = 62

            if entry["extended"] and (index["version"] == 3):
                entry["extra-flags"] = read("H")
                # 1-bit reserved
                entry["reserved"] = bool(entry["extra-flags"] & (0b10000000 << 8))
                # 1-bit skip-worktree
                entry["skip-worktree"] = bool(entry["extra-flags"] & (0b01000000 << 8))
                # 1-bit intent-to-add
                entry["intent-to-add"] = bool(entry["extra-flags"] & (0b00100000 << 8))
                # 13-bits unused
                # used = entry["extra-flags"] & (0b11100000 << 8)
                # check(not used, "Expected unused bits in extra-flags")
                entrylen += 2

            if namelen < 0xFFF:
                entry["name"] = f.read(namelen).decode("utf-8", "replace")
                entrylen += namelen
            else:
                # Do it the hard way
                name = []
                while True:
                    byte = f.read(1)
                    if byte == "\x00":
                        break
                    name.append(byte)
                entry["name"] = b"".join(name).decode("utf-8", "replace")
                entrylen += 1

            padlen = (8 - (entrylen % 8)) or 8
            nuls = f.read(padlen)
            check(set(nuls) == set(['\x00']), "padding contained non-NUL")
            
            yield entry
                
        f.close()





