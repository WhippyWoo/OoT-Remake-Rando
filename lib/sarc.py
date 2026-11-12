# Minimal SARC archive reader (used to unpack the zstd dictionaries from Pack/ZsDic.pack.zs).
import struct
def sarc_file_offsets(data):
    """{name: (start, end)} byte ranges of each file inside a SARC archive."""
    e='<' if data[6:8]==b'\xff\xfe' else '>'
    hdr=struct.unpack(e+'H',data[4:6])[0]; dstart=struct.unpack(e+'I',data[0xC:0x10])[0]
    o=hdr; cnt=struct.unpack(e+'H',data[o+6:o+8])[0]; o+=12
    nodes=[struct.unpack(e+'IIII',data[o+i*16:o+i*16+16]) for i in range(cnt)]
    o+=cnt*16; nt=o+8; out={}
    for h,attr,s,en in nodes:
        noff=(attr&0xFFFF)*4; out[data[nt+noff:data.index(b'\0',nt+noff)].decode()]=(dstart+s,dstart+en)
    return out

def sarc_files(data):
    assert data[:4]==b'SARC'
    bom=data[6:8]; e='<' if bom==b'\xff\xfe' else '>'
    hdr=struct.unpack(e+'H',data[4:6])[0]
    dstart=struct.unpack(e+'I',data[0xC:0x10])[0]
    o=hdr; assert data[o:o+4]==b'SFAT'
    cnt=struct.unpack(e+'H',data[o+6:o+8])[0]; o+=12
    nodes=[struct.unpack(e+'IIII',data[o+i*16:o+i*16+16]) for i in range(cnt)]
    o+=cnt*16; assert data[o:o+4]==b'SFNT'; nt=o+8
    out={}
    for h,attr,s,en in nodes:
        noff=(attr&0xFFFF)*4; n=data[nt+noff:data.index(b'\0',nt+noff)].decode()
        out[n]=data[dstart+s:dstart+en]
    return out

def sarc_replace(data,changes):
    """A copy of a SARC archive with some files' contents replaced ({name: bytes}). File order, names and hashes stay;
    file data keeps its order, and each file keeps the alignment it had (so the game's alignment rules still hold)."""
    assert data[:4]==b'SARC' and data[6:8]==b'\xff\xfe', 'little-endian SARC expected'
    hdr=struct.unpack('<H',data[4:6])[0]; dstart=struct.unpack('<I',data[0xC:0x10])[0]
    o=hdr; cnt=struct.unpack('<H',data[o+6:o+8])[0]; o+=12
    nodes=[list(struct.unpack('<IIII',data[o+i*16:o+i*16+16])) for i in range(cnt)]
    nt=o+cnt*16+8; names=[]
    for h,attr,s,e in nodes:
        noff=(attr&0xFFFF)*4; names.append(data[nt+noff:data.index(b'\0',nt+noff)].decode())
    unknown=set(changes)-set(names)
    if unknown: raise KeyError('not in archive: %s'%', '.join(sorted(unknown)))
    def alignment(off):
        a=1
        while a<0x2000 and off%(a*2)==0: a*=2
        return a
    out=bytearray(data[:dstart]); pos=0
    for i in sorted(range(cnt),key=lambda i:nodes[i][2]):   # data in its original order
        h,attr,s,e=nodes[i]; content=changes.get(names[i],data[dstart+s:dstart+e])
        a=alignment(dstart+s); start=(dstart+pos+a-1)//a*a-dstart
        out+=bytes(start-pos)+content; nodes[i][2]=start; nodes[i][3]=start+len(content); pos=start+len(content)
    for i,n in enumerate(nodes): struct.pack_into('<IIII',out,hdr+12+i*16,*n)
    struct.pack_into('<I',out,8,len(out))
    return bytes(out)
