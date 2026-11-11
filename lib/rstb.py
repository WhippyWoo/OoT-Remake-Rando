# TotK-style RESTBL reader/writer. Keys: crc32 of the romfs path without .zs (plus a small name table for collisions).
import struct,zlib
class Rstb:
    def __init__(s,d):
        assert d[:6]==b'RESTBL'
        s.ver,s.slen,nc,nn=struct.unpack_from('<IIII',d,6); o=22
        s.crc={}
        for i in range(nc): c,v=struct.unpack_from('<II',d,o+8*i); s.crc[c]=v
        o+=8*nc; s.names={}
        for i in range(nn):
            n=d[o:o+s.slen].split(b'\0')[0].decode(); s.names[n]=struct.unpack_from('<I',d,o+s.slen)[0]; o+=s.slen+4
    def get(s,path):
        if path in s.names: return s.names[path]
        return s.crc.get(zlib.crc32(path.encode()))
    def set(s,path,v):
        if path in s.names: s.names[path]=v
        else: s.crc[zlib.crc32(path.encode())]=v
    def build(s):
        out=bytearray(b'RESTBL'+struct.pack('<IIII',s.ver,s.slen,len(s.crc),len(s.names)))
        for c in sorted(s.crc): out+=struct.pack('<II',c,s.crc[c])
        for n in sorted(s.names): out+=n.encode().ljust(s.slen,b'\0')+struct.pack('<I',s.names[n])
        return bytes(out)
