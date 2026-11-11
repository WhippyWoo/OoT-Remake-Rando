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
