# Read-only BFEVFL (v0.4, TotK-style) event flow reader.
# Layout notes: pointers are file offsets to u16-length-prefixed strings; actor 0x38 bytes, event 0x30 bytes,
# entry point 0x20 bytes (main event index at +0x1c); switch cases are (u32 value, u16 event) pairs, and for
# bool queries case value 0 means "true".
import struct
class Evfl:
    def __init__(s,d):
        assert d[:6]==b'BFEVFL'; s.d=d
        nflow,ntl=struct.unpack_from('<HH',d,0x20)
        s.actors=[]; s.events=[]; s.entry_points={}; s.clips=[]; s.name=''; s.kind='timeline' if ntl and not nflow else 'flowchart'
        if nflow: s._flowchart(s.q(s.q(0x28)))
        if ntl: s._timeline(s.q(s.q(0x38)))
    def _actors(s,p,n):
        out=[]
        for i in range(n):
            a=p+0x38*i; nacts,nqs=struct.unpack_from('<HH',s.d,a+0x30)
            out.append(dict(name=s.str(s.q(a)),sub=s.str(s.q(a+8)),
                actions=[s.str(s.q(s.q(a+0x18)+8*k)) for k in range(nacts)],
                queries=[s.str(s.q(s.q(a+0x20)+8*k)) for k in range(nqs)]))
        return out
    def _flowchart(s,fl):
        d=s.d; assert d[fl:fl+4]==b'EVFL'; s.fl=fl
        na,nact,nq,nev,nep=struct.unpack_from('<5H',d,fl+0x10)
        s.name=s.str(s.q(fl+0x20)); s.actors=s._actors(s.q(fl+0x28),na)
        for i in range(nev):
            e=s.q(fl+0x30)+0x30*i; t=d[e+8]; ev=dict(idx=i,name=s.str(s.q(e)),type=t,off=e)
            if t==0:
                nxt,ac,act=struct.unpack_from('<HHH',d,e+0xa); ev.update(kind='action',next=nxt,actor=ac,action=act,params=s.container(s.q(e+0x10)))
            elif t==1:
                nc,ac,qu=struct.unpack_from('<HHH',d,e+0xa); co=s.q(e+0x18)
                ev.update(kind='switch',actor=ac,query=qu,params=s.container(s.q(e+0x10)),
                    cases=[struct.unpack_from('<IH',d,co+8*k) for k in range(nc)])
            else:
                ev.update(kind={2:'fork',3:'join',4:'subflow'}.get(t,'?%d'%t))
            s.events.append(ev)
        names=s.dic(s.q(fl+0x38)); ep=s.q(fl+0x40)
        s.entry_points={n:struct.unpack_from('<H',d,ep+0x20*k+0x1c)[0] for k,n in enumerate(names)}
    def _timeline(s,tl):
        d=s.d; assert d[tl:tl+4]==b'TLIN'; s.tl=tl
        na,nact,nclip=struct.unpack_from('<3H',d,tl+0x14)
        s.name=s.str(s.q(tl+0x20)); s.tl_actors=s._actors(s.q(tl+0x28),na)
        for i in range(nclip):
            c=s.q(tl+0x30)+0x18*i; start,dur=struct.unpack_from('<ff',d,c); ac,act=struct.unpack_from('<HH',d,c+8)
            s.clips.append(dict(idx=i,off=c,start=start,duration=dur,actor=ac,action=act,params=s.container(s.q(c+0x10))))
    def q(s,o): return struct.unpack_from('<Q',s.d,o)[0]
    def str(s,p):
        if not p: return ''
        n=struct.unpack_from('<H',s.d,p)[0]; return s.d[p+2:p+2+n].decode('utf8','replace')
    def dic(s,p):
        if not p: return []
        n=struct.unpack_from('<i',s.d,p+4)[0]
        return [s.str(s.q(p+8+0x10*(k+1)+8)) for k in range(n)]
    def container(s,p):
        if not p: return None
        t,n=s.d[p],struct.unpack_from('<H',s.d,p+2)[0]
        if t==1:
            keys=s.dic(s.q(p+8)); return {keys[k]:s.container(s.q(p+0x10+8*k)) for k in range(n)}
        if t in (0,5): return s.str(s.q(p+0x10)) if n==1 else [s.str(s.q(p+0x10+8*k)) for k in range(n)]
        if t==2: v=struct.unpack_from('<%di'%n,s.d,p+0x10); return v[0] if n==1 else list(v)
        if t==3: v=struct.unpack_from('<%dI'%n,s.d,p+0x10); return bool(v[0]) if n==1 else [bool(x) for x in v]
        if t==4: v=struct.unpack_from('<%df'%n,s.d,p+0x10); return v[0] if n==1 else list(v)
        if t==12: return ('actor',s.str(s.q(p+0x10)),s.str(s.q(p+0x18)))
        return ('type%d'%t,n)

    def successors(s,ev):
        """Event indices that can follow this event."""
        H=lambda o: struct.unpack_from('<H',s.d,o)[0]; o=ev['off']
        if ev['kind']=='action': out=[ev['next']]
        elif ev['kind']=='switch': out=[c[1] for c in ev['cases']]
        elif ev['kind']=='fork': p=s.q(o+0x10); out=[H(p+2*k) for k in range(H(o+0xa))]+[H(o+0xc)]
        else: out=[H(o+0xa)]
        return [i for i in out if i!=0xffff]
    def subflow(s,ev):
        """(entry point name, parameters) of a subflow event."""
        return s.str(s.q(ev['off']+0x20)),s.container(s.q(ev['off']+0x10))
    def walk(s,entry):
        """All events reachable from an entry point, in visiting order."""
        seen=[]; todo=[s.entry_points[entry]]
        while todo:
            i=todo.pop(0)
            if i in seen: continue
            seen.append(i); todo+=s.successors(s.events[i])
        return [s.events[i] for i in seen]

    def param_ref(s,container_ptr,key):
        """File offset of a parameter's value inside a parameter container, plus its type code."""
        n=struct.unpack_from('<H',s.d,container_ptr+2)[0]; keys=s.dic(s.q(container_ptr+8))
        p=s.q(container_ptr+0x10+8*keys.index(key)); return p+0x10,s.d[p]


class EvflWriter:
    """Changes parameter values in a BFEVFL file. New strings are appended to the end of the string pool,
    so no existing pointer moves; only the relocation table behind the pool shifts."""
    def __init__(s,data):
        s.d=bytearray(data); I=lambda o: struct.unpack_from('<I',s.d,o)[0]
        s.rlt=I(0x18); assert s.d[s.rlt:s.rlt+4]==b'RELT' and I(s.rlt+8)==1, 'expected one relocation section'
        sec=s.rlt+0x10; s.end=I(sec+8)+I(sec+12)          # end of the data covered by relocation = end of string pool
        s.str_hdr=s.d.find(b'STR ',0,s.rlt); assert s.str_hdr>0
        s.strings={}; o=s.str_hdr+0x18
        for _ in range(I(s.str_hdr+0x10)):
            n=struct.unpack_from('<H',s.d,o)[0]; s.strings.setdefault(s.d[o+2:o+2+n].decode('utf8'),o); o+=(2+n+1+1)&~1
        s.added=bytearray()
    def string(s,text):
        """Pointer to a pool string, appending it if the file doesn't have it yet."""
        if text not in s.strings:
            pos=((s.end+1)&~1)+len(s.added)
            b=text.encode('utf8'); entry=struct.pack('<H',len(b))+b+b'\0'
            if len(entry)%2: entry+=b'\0'
            s.strings[text]=pos; s.added+=entry
        return s.strings[text]
    def set_string(s,field_off,text): struct.pack_into('<Q',s.d,field_off,s.string(text))
    def set_int(s,field_off,value): struct.pack_into('<i',s.d,field_off,value)
    def build(s):
        if not s.added: return bytes(s.d)
        I=lambda o: struct.unpack_from('<I',s.d,o)[0]
        body=s.d[:(s.end+1)&~1]+s.added; new_end=len(body).__index__()
        # the last appended string ends with a padding byte when needed; the covered size ends at its terminator
        body+=b'\0'*((-len(body))%8); rlt=bytearray(s.d[s.rlt:])
        struct.pack_into('<I',rlt,4,len(body))                      # RELT self offset
        struct.pack_into('<I',rlt,0x10+12,new_end-I(s.rlt+0x10+8))  # section size
        out=bytearray(body)+rlt
        struct.pack_into('<I',out,0x18,len(body)); struct.pack_into('<I',out,0x1c,len(out))
        cnt=I(s.str_hdr+0x10)+len([k for k,v in s.strings.items() if v>=s.end])
        struct.pack_into('<I',out,s.str_hdr+0x10,cnt)
        return bytes(out)
