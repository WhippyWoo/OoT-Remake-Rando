# Typed BYML v7 reader + writer (little endian). Values keep their exact BYML type so files rebuild faithfully.
import struct
class T:  # typed scalar wrapper
    __slots__=('t','v')
    def __init__(s,t,v): s.t=t; s.v=v
    def __eq__(s,o): return isinstance(o,T) and s.t==o.t and s.v==o.v
    def __repr__(s): return 'T(%x,%r)'%(s.t,s.v)
class HMap(dict):  # 0x20 / 0x21 hash-keyed map
    def __init__(s,t,*a): super().__init__(*a); s.t=t
STR,BIN,BINA,ARR,DICT,BOOL,INT,FLT,UINT,I64,U64,DBL,NULL=0xA0,0xA1,0xA2,0xC0,0xC1,0xD0,0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xFF

def read(d):
    """Returns (version, root). Little-endian ('YB') files are the default; big-endian ('BY') files
    (e.g. GameDataList) come back with root wrapped as BigEndian so write() keeps their byte order."""
    assert d[:2] in (b'YB',b'BY'); e='<' if d[:2]==b'YB' else '>'; bo='little' if e=='<' else 'big'
    ver,hk,st,root=struct.unpack_from(e+'HIII',d,2)
    u=lambda f,o: struct.unpack_from(e+f,d,o)[0]
    u24=lambda o: int.from_bytes(d[o:o+3],bo)
    def strtab(o):
        if not o: return []
        n=u24(o+1); return [d[o+u('I',o+4+4*i):d.index(b'\0',o+u('I',o+4+4*i))].decode('utf8') for i in range(n)]
    keys,strs=strtab(hk),strtab(st)
    def val(t,v):
        if t==STR: return strs[v]
        if t==BOOL: return bool(v)
        if t==INT: return struct.unpack('<i',struct.pack('<I',v))[0]   # value already decoded with the file's byte order
        if t==FLT: return T(FLT,v)  # keep raw bits
        if t==UINT: return T(UINT,v)
        if t in (I64,U64,DBL): return T(t,u('Q',v))
        if t==NULL: return None
        if t==BIN: n=u('I',v); return T(BIN,d[v+4:v+4+n])
        if t==BINA: n=u('I',v); return T(BINA,(u('I',v+4),d[v+8:v+8+n]))
        return node(t,v)
    def node(t,o):
        n=u24(o+1)
        if t==ARR:
            ts=d[o+4:o+4+n]; vo=o+4+((n+3)&~3); return [val(ts[i],u('I',vo+4*i)) for i in range(n)]
        if t==DICT:
            return {keys[u24(o+4+8*i)]:val(d[o+7+8*i],u('I',o+8+8*i)) for i in range(n)}
        if t in (0x20,0x21):
            ks=4 if t==0x20 else 8; es=ks+4; tb=o+4+es*n; m=HMap(t)
            for i in range(n):
                e=o+4+es*i; m[u('I' if ks==4 else 'Q',e)]=val(d[tb+i],u('I',e+ks))
            return m
        raise ValueError('node %x'%t)
    r=node(d[root],root)
    return (ver,BigEndian(r)) if e=='>' else (ver,r)

class BigEndian:
    """Marks a root read from a big-endian file; .root is the data."""
    def __init__(s,root): s.root=root
    def __eq__(s,o): return isinstance(o,BigEndian) and s.root==o.root

def write(root,ver=7):
    e='<'
    if isinstance(root,BigEndian): root=root.root; e='>'
    bo='little' if e=='<' else 'big'
    keys,strs=set(),set()
    def scan(x):
        if isinstance(x,str): strs.add(x)
        elif isinstance(x,dict):
            if not isinstance(x,HMap): keys.update(x.keys())
            for v in x.values(): scan(v)
        elif isinstance(x,list):
            for v in x: scan(v)
    scan(root)
    keys=sorted(keys,key=lambda s:s.encode()); strs=sorted(strs,key=lambda s:s.encode())
    ki={k:i for i,k in enumerate(keys)}; si={s:i for i,s in enumerate(strs)}
    out=bytearray(16)
    memo={}; kc={}
    def key(x):  # structural key so identical nodes/values are written once and shared
        i=id(x)
        if i in kc: return kc[i][0]
        if isinstance(x,T): k=(x.t,x.v)
        elif isinstance(x,HMap): k=('H',x.t,tuple((h,key(v)) for h,v in sorted(x.items())))
        elif isinstance(x,dict): k=('D',tuple((kk,key(v)) for kk,v in sorted(x.items())))
        elif isinstance(x,list): k=('L',tuple(key(v) for v in x))
        else: k=(type(x).__name__,x)
        kc[i]=(k,x); return k
    def align(a):
        while len(out)%a: out.append(0)
    def strtab(lst):
        if not lst: return 0
        align(4); o=len(out); n=len(lst)
        out.extend(bytes([0xC2])+n.to_bytes(3,bo)); tbl=len(out); out.extend(bytes(4*(n+1)))
        for i,s in enumerate(lst):
            struct.pack_into(e+'I',out,tbl+4*i,len(out)-o); out.extend(s.encode()+b'\0')
        struct.pack_into(e+'I',out,tbl+4*n,len(out)-o); return o
    hk=strtab(keys); st=strtab(strs)
    def typ(x):
        if isinstance(x,T): return x.t
        if isinstance(x,bool): return BOOL
        if isinstance(x,int): return INT
        if isinstance(x,str): return STR
        if x is None: return NULL
        if isinstance(x,HMap): return x.t
        if isinstance(x,dict): return DICT
        if isinstance(x,list): return ARR
        raise TypeError(type(x))
    def value(x):  # returns u32 stored in parent (inline value or offset)
        t=typ(x)
        if t==STR: return si[x]
        if t==BOOL: return int(x)
        if t==INT: return x&0xFFFFFFFF
        if t in (FLT,UINT): return x.v
        if t==NULL: return 0
        if t in (I64,U64,DBL,BIN,BINA,ARR,DICT,0x20,0x21):
            k=key(x)
            if k in memo: return memo[k]
            memo[k]=r=_value(x,t); return r
        raise TypeError(t)
    def _value(x,t):
        if t in (I64,U64,DBL):
            align(4); o=len(out); out.extend(struct.pack(e+'Q',x.v)); return o
        if t==BIN:
            align(4); o=len(out); out.extend(struct.pack(e+'I',len(x.v))+x.v); return o
        if t==BINA:
            align(4); o=len(out); out.extend(struct.pack(e+'II',len(x.v[1]),x.v[0])+x.v[1]); return o
        return container(x,t)
    def container(x,t):
        align(4); o=len(out); n=len(x)
        out.extend(bytes([t])+n.to_bytes(3,bo))
        if t==ARR:
            out.extend(bytes(typ(v) for v in x)); align(4); vo=len(out); out.extend(bytes(4*n))
            for i,v in enumerate(x): r=value(v); struct.pack_into(e+'I',out,vo+4*i,r)
        elif t==DICT:
            items=sorted(x.items(),key=lambda kv:ki[kv[0]]); eo=len(out); out.extend(bytes(8*n))
            for i,(k,v) in enumerate(items):
                out[eo+8*i:eo+8*i+3]=ki[k].to_bytes(3,bo); out[eo+8*i+3]=typ(v); r=value(v); struct.pack_into(e+'I',out,eo+8*i+4,r)
        else:
            ks=4 if t==0x20 else 8; items=sorted(x.items()); eo=len(out); out.extend(bytes((ks+4)*n))
            out.extend(bytes(typ(v) for k,v in items)); align(4)
            for i,(k,v) in enumerate(items):
                struct.pack_into(e+('I' if ks==4 else 'Q'),out,eo+(ks+4)*i,k); r=value(v); struct.pack_into(e+'I',out,eo+(ks+4)*i+ks,r)
        return o
    r=container(root,typ(root))
    struct.pack_into(e+'2sHIII',out,0,b'YB' if e=='<' else b'BY',ver,hk,st,r)
    align(4); return bytes(out)
