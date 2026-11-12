# AINB (AI node graph, version 0x408) reader/writer.
# Layout follows the EPD wiki and tomolib: a 0x74-byte header of section offsets, commands (0x18), nodes (0x3C),
# blackboard, one parameter block per node, then property, I/O, multi-input, transition, query, EXB, module, action,
# blackboard-id, replacement, 0x6C, enum and string sections. Every pointer is an absolute file offset, so the
# writer lays the sections out again and fixes them. Strings keep their offsets; new ones go at the end of the pool.
# Files with attachments or the 0x58 section aren't supported (none of the chest graphs use them).
import struct

HEADER=['magic','version','filename','commands','nodes','queries','attachments','outputs','blackboard','strings',
        'enums','properties','transitions','io','multi','attachment_table','attachment_index','exb','replacement',
        'query','x50','x54','x58','module','category_name','category','action','x6c','blackboard_id']
PTYPES=('int','bool','float','string','vec3','pointer')
INPUT_PLUG={0:5,1:0,3:4}   # plug type that links an input of this parameter type to its source node (int, bool, string)
BB_VALUE_SIZE=(4,4,4,4,4,12,0)   # blackboard types: string, int, (u32 / float), bool, vec3, pointer
PROP_SIZE=(12,12,12,12,20,12); IN_SIZE=(16,16,16,16,24,20); OUT_SIZE=(4,4,4,4,4,8)

class Node:
    """One node: the fixed 0x3C-byte entry plus its parameter block.
    props[t] / inputs[t] / outputs[t]: (base, count) into the global per-type arrays.
    plugs: list of (plug type 0-9, raw plug bytes); the raw bytes start with the target node index (s32)."""
    def __init__(s,entry,block=None):
        s.entry=bytearray(entry); s.props=[]; s.inputs=[]; s.outputs=[]; s.plugs=[]
        if block is None: return
        d,base=block
        for t in range(6): s.props.append(list(struct.unpack_from('<II',d,base+8*t)))
        for t in range(6):
            ib,ic,ob,oc=struct.unpack_from('<4I',d,base+0x30+16*t); s.inputs.append([ib,ic]); s.outputs.append([ob,oc])
        pairs=[struct.unpack_from('<BB',d,base+0x90+2*k) for k in range(10)]
        ptrs=[]
        for k,(cnt,b) in enumerate(pairs):
            for j in range(cnt): ptrs.append((k,struct.unpack_from('<I',d,base+0xA4+4*(b+j))[0]))
        s._ptrs=ptrs
    type=property(lambda s: struct.unpack_from('<H',s.entry,0)[0])
    index=property(lambda s: struct.unpack_from('<H',s.entry,2)[0])
    flags=property(lambda s: s.entry[6])
    name_off=property(lambda s: struct.unpack_from('<I',s.entry,8)[0])
    def field(s,fmt,off,value=None):
        if value is None: return struct.unpack_from(fmt,s.entry,off)[0]
        struct.pack_into(fmt,s.entry,off,value)
    def block(s,base):
        """The parameter block, written at file offset `base`."""
        out=bytearray()
        for b,c in s.props: out+=struct.pack('<II',b,c)
        for (ib,ic),(ob,oc) in zip(s.inputs,s.outputs): out+=struct.pack('<4I',ib,ic,ob,oc)
        counts=[0]*10
        for k,_ in s.plugs: counts[k]+=1
        run=0
        for k in range(10): out+=struct.pack('<BB',counts[k],run); run+=counts[k]   # (count, first index) per plug type
        order=sorted(range(len(s.plugs)),key=lambda i:s.plugs[i][0])   # the pointer array is grouped by plug type
        ptr=base+len(out)+4*len(s.plugs); table=b''; blob=b''
        for i in order:
            table+=struct.pack('<I',ptr); blob+=s.plugs[i][1]; ptr+=len(s.plugs[i][1])
        return bytes(out+table+blob)

class Ainb:
    def __init__(s,data):
        d=bytes(data); s.h=dict(zip(HEADER,struct.unpack_from('<4s28I',d,0))); h=s.h
        if h['magic']!=b'AIB ' or h['version']!=0x408: raise ValueError('not an AINB 0x408 file')
        if h['attachments'] or h['x58']: raise ValueError('attachments / 0x58 section not supported')
        s.commands=d[0x74:0x74+0x18*h['commands']]
        no=0x74+0x18*h['commands']
        entries=[d[no+0x3C*i:no+0x3C*(i+1)] for i in range(h['nodes'])]
        bodies=[struct.unpack_from('<I',e,0x14)[0] for e in entries]
        for e in entries:
            if struct.unpack_from('<I',e,0x28)[0]: raise ValueError('0x58 section not supported')
        s.nodes=[Node(e,(d,b)) for e,b in zip(entries,bodies)]
        ends=sorted(set(bodies))+[h['attachment_table']]
        for n,b in zip(s.nodes,bodies):
            end=ends[ends.index(b)+1]
            ptrs=n._ptrs; del n._ptrs
            order=sorted(range(len(ptrs)),key=lambda i:ptrs[i][1])
            spans={}
            for j,i in enumerate(order):
                start=ptrs[i][1]; stop=ptrs[order[j+1]][1] if j+1<len(order) else end
                if not b<=start<=stop<=end: raise ValueError('plug outside its block')
                spans[i]=d[start:stop]
            n.plugs=[(ptrs[i][0],spans[i]) for i in range(len(ptrs))]
            if n.block(b)!=d[b:end]: raise ValueError('node %d block does not round-trip'%n.index)
        s.blackboard=d[h['blackboard']:min(bodies) if bodies else h['attachment_table']]
        if h['attachment_index']!=h['attachment_table'] or h['properties']!=h['attachment_index']:
            raise ValueError('attachment data not supported')
        # properties: six pointers, then per-type arrays
        pt=struct.unpack_from('<6I',d,h['properties']); bounds=list(pt)+[h['io']]
        s.props=[[d[o:o+PROP_SIZE[t]] for o in range(bounds[t],bounds[t+1],PROP_SIZE[t])] for t in range(6)]
        # I/O: six (inputs, outputs) pointer pairs, then for each type its inputs and outputs
        io=struct.unpack_from('<12I',d,h['io']); bounds=list(io)+[h['multi']]
        s.inputs=[[d[o:o+IN_SIZE[t]] for o in range(bounds[2*t],bounds[2*t+1],IN_SIZE[t])] for t in range(6)]
        s.outputs=[[d[o:o+OUT_SIZE[t]] for o in range(bounds[2*t+1],bounds[2*t+2],OUT_SIZE[t])] for t in range(6)]
        s.multi=d[h['multi']:h['transitions']]
        # transitions: pointer table (its length is given by the first pointer), then records
        tr=d[h['transitions']:h['x50']]; s.trans_ptrs=[]; s.trans_data=b''
        if tr:
            first=struct.unpack_from('<I',tr,0)[0]; n=(first-h['transitions'])//4
            s.trans_ptrs=[struct.unpack_from('<I',tr,4*i)[0]-first for i in range(n)]; s.trans_data=tr[4*n:]
        s.x50=d[h['x50']:h['query']]
        s.queries=d[h['query']:h['exb'] or h['module']]
        s.exb=d[h['exb']:h['module']] if h['exb'] else b''
        s.module=d[h['module']:h['action']]; s.action=d[h['action']:h['blackboard_id']]
        s.bbid=d[h['blackboard_id']:h['replacement']]; s.replacement=d[h['replacement']:h['x6c']]
        s.x6c=d[h['x6c']:h['enums']]; s.enums=d[h['enums']:h['strings']]; s.pool=bytearray(d[h['strings']:])
        if s.build()!=d: raise ValueError('file does not round-trip')

    def string(s,text):
        """Offset of a string in the pool, adding it at the end if new."""
        b=text.encode()+b'\0'; i=s.pool.find(b)
        while i>0 and s.pool[i-1]!=0: i=s.pool.find(b,i+1)
        if i<0: i=len(s.pool); s.pool+=b
        return i
    def str_at(s,off): return s.pool[off:s.pool.index(0,off)].decode()

    # ---- editing ----
    def query_ids(s):
        """{node index: query id}: query nodes (flag bit 0) are numbered in node order."""
        ids={}
        for i,n in enumerate(s.nodes):
            if n.flags&1: ids[i]=len(ids)
        return ids
    def node_queries(s,i):
        b,c=s.nodes[i].field('<H',0x24),s.nodes[i].field('<H',0x26)
        ids={v:k for k,v in s.query_ids().items()}
        return [ids[struct.unpack_from('<H',s.queries,4*j)[0]] for j in range(b,b+c)]
    def set_node_queries(s,i,nodes):
        """The query nodes node i reads from (written as a new run at the end of the query array)."""
        ids=s.query_ids(); base=len(s.queries)//4
        s.queries+=b''.join(struct.pack('<HH',ids[n],0) for n in nodes)
        s.nodes[i].field('<H',0x24,base if nodes else 0); s.nodes[i].field('<H',0x26,len(nodes))
    def add_node(s,template):
        """Append a copy of node `template` (its parameters copied too, its links and queries cleared). Returns its index."""
        src=s.nodes[template]; n=Node(src.entry); i=len(s.nodes)
        n.field('<H',2,i); n.entry[0x2C+12:0x2C+16]=struct.pack('<I',0x52414e44+i)   # GUID (debug only): keep it unique
        for t in range(6):
            b,c=src.props[t]; n.props.append([len(s.props[t]),c]); s.props[t]+=s.props[t][b:b+c]
            b,c=src.inputs[t]; n.inputs.append([len(s.inputs[t]),c]); s.inputs[t]+=s.inputs[t][b:b+c]
            b,c=src.outputs[t]; n.outputs.append([len(s.outputs[t]),c]); s.outputs[t]+=s.outputs[t][b:b+c]
        for t in range(6):   # an input copied from a linked one starts unlinked
            b,c=n.inputs[t]
            for j in range(b,b+c):
                e=bytearray(s.inputs[t][j])
                if struct.unpack_from('<h',e,4)[0]>=0: struct.pack_into('<hhI',e,4,-1,0,0); s.inputs[t][j]=bytes(e)
        n.field('<H',0x24,0); n.field('<H',0x26,0)
        s.nodes.append(n); s.h['queries']=sum(1 for x in s.nodes if x.flags&1)
        return i
    def _input(s,i,ptype,name):
        b,c=s.nodes[i].inputs[ptype]
        for j in range(b,b+c):
            if s.str_at(struct.unpack_from('<I',s.inputs[ptype][j],0)[0])==name: return j
        raise KeyError('node %d has no %s input %s'%(i,PTYPES[ptype],name))
    def link_input(s,i,ptype,name,src,src_out=0):
        """Feed input `name` of node i from output `src_out` of node `src` (and add the matching plug)."""
        j=s._input(i,ptype,name); e=bytearray(s.inputs[ptype][j])
        struct.pack_into('<hhI',e,4,src,src_out,0); s.inputs[ptype][j]=bytes(e)
        n=s.nodes[i]; n.plugs=[p for p in n.plugs if not (p[0]==INPUT_PLUG[ptype] and s.str_at(struct.unpack_from('<I',p[1],4)[0])==name)]
        n.plugs.append((INPUT_PLUG[ptype],struct.pack('<iI',src,s.string(name))))
    def input_from_blackboard(s,i,ptype,name,bb_index):
        """Read input `name` of node i from blackboard parameter `bb_index` (index within its type)."""
        j=s._input(i,ptype,name); e=bytearray(s.inputs[ptype][j])
        struct.pack_into('<hhI',e,4,-1,0,0x80000000|bb_index); s.inputs[ptype][j]=bytes(e)

    def input_constant(s,i,ptype,name,text,flags=0x800000):
        """Make string input `name` of node i a constant (flags as the game's own constant string inputs)."""
        j=s._input(i,ptype,name); e=bytearray(s.inputs[ptype][j])
        struct.pack_into('<hhII',e,4,-1,0,flags,s.string(text)); s.inputs[ptype][j]=bytes(e)

    # ---- blackboard ----
    def _bb(s):
        bb=s.blackboard; hdr=[list(struct.unpack_from('<HHHH',bb,8*t)) for t in range(7)]
        total=sum(h[0] for h in hdr); vb=56+8*total
        params=[]   # per type: list of (flags, notes, value bytes)
        for t,(cnt,base,voff,_) in enumerate(hdr):
            params.append([(*struct.unpack_from('<II',bb,56+8*(base+k)),bb[vb+voff+BB_VALUE_SIZE[t]*k:vb+voff+BB_VALUE_SIZE[t]*(k+1)]) for k in range(cnt)])
        refs=bb[vb+hdr[5][2]+12*hdr[5][0]:]
        return params,refs
    def blackboard_params(s,ptype):
        params,_=s._bb(); return [s.str_at(f&0x3fffff) for f,_,_ in params[ptype]]
    def build(s):
        h=dict(s.h); out=bytearray(0x74)
        out+=s.commands
        node_pos=len(out); out+=bytes(0x3C*len(s.nodes))
        h['blackboard']=len(out); out+=s.blackboard
        for i,n in enumerate(s.nodes):
            n.field('<I',0x14,len(out)); out+=n.block(len(out))
            out[node_pos+0x3C*i:node_pos+0x3C*(i+1)]=n.entry
        h['attachment_table']=h['attachment_index']=h['properties']=len(out)
        sizes=[len(a)*PROP_SIZE[t] for t,a in enumerate(s.props)]; p=len(out)+24; ptrs=[]
        for sz in sizes: ptrs.append(p); p+=sz
        out+=struct.pack('<6I',*ptrs)
        for a in s.props: out+=b''.join(a)
        h['io']=len(out); p=len(out)+48; ptrs=[]
        for t in range(6):
            ptrs.append(p); p+=len(s.inputs[t])*IN_SIZE[t]; ptrs.append(p); p+=len(s.outputs[t])*OUT_SIZE[t]
        out+=struct.pack('<12I',*ptrs)
        for t in range(6): out+=b''.join(s.inputs[t])+b''.join(s.outputs[t])
        h['multi']=len(out); out+=s.multi
        h['transitions']=len(out)
        if s.trans_ptrs:
            first=len(out)+4*len(s.trans_ptrs)
            out+=b''.join(struct.pack('<I',first+r) for r in s.trans_ptrs)+s.trans_data
        h['x50']=len(out); out+=s.x50
        h['query']=len(out); out+=s.queries
        if s.exb: h['exb']=len(out); out+=s.exb
        h['module']=len(out); out+=s.module; h['action']=len(out); out+=s.action
        h['blackboard_id']=len(out); out+=s.bbid; h['replacement']=len(out); out+=s.replacement
        h['x6c']=len(out); out+=s.x6c; h['enums']=len(out); out+=s.enums
        h['strings']=len(out); out+=s.pool
        h['nodes']=len(s.nodes)
        out[0:0x74]=struct.pack('<4s28I',*[h[k] for k in HEADER])
        return bytes(out)
