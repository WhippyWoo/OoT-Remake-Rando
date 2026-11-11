# zstd compression with whatever is available: Python 3.14's built-in compression.zstd, the 'zstandard'
# package (pip install zstandard), or the zstd command-line tool. All three give the same file format.
# Output frames always record the uncompressed size (single segment) and have no checksum, like Nintendo's files;
# without the size the game hangs on its boot loading screen.
import shutil,subprocess

def backend():
    try:
        from compression import zstd   # noqa: F401  (Python 3.14+)
        return 'python'
    except ImportError: pass
    try:
        import zstandard   # noqa: F401
        return 'zstandard'
    except ImportError: pass
    return 'cli' if shutil.which('zstd') else None

BACKEND=backend()
_dicts={}
def _dict_bytes(path):
    if path not in _dicts: _dicts[path]=open(path,'rb').read()
    return _dicts[path]

def decompress(data,dict_path=None):
    if BACKEND=='python':
        from compression import zstd
        return zstd.decompress(data,zstd_dict=zstd.ZstdDict(_dict_bytes(dict_path)) if dict_path else None)
    if BACKEND=='zstandard':
        import zstandard
        d=zstandard.ZstdCompressionDict(_dict_bytes(dict_path)) if dict_path else None
        return zstandard.ZstdDecompressor(dict_data=d).decompress(data)
    if BACKEND=='cli':
        cmd=['zstd','-q','-d','-c']+(['-D',dict_path] if dict_path else [])
        return subprocess.run(cmd,input=data,capture_output=True,check=True).stdout
    raise RuntimeError('no zstd support found: install Python 3.14+, or run: pip install zstandard')

def compress(data,dict_path=None):
    if BACKEND=='python':
        from compression import zstd
        P=zstd.CompressionParameter
        return zstd.compress(data,options={P.compression_level:19,P.checksum_flag:0,P.content_size_flag:1},
                             zstd_dict=zstd.ZstdDict(_dict_bytes(dict_path)) if dict_path else None)
    if BACKEND=='zstandard':
        import zstandard
        d=zstandard.ZstdCompressionDict(_dict_bytes(dict_path)) if dict_path else None
        return zstandard.ZstdCompressor(level=19,dict_data=d,write_checksum=False,write_content_size=True).compress(data)
    if BACKEND=='cli':
        cmd=['zstd','-q','-19','--no-check','--stream-size=%d'%len(data),'-c']+(['-D',dict_path] if dict_path else [])
        return subprocess.run(cmd,input=data,capture_output=True,check=True).stdout
    raise RuntimeError('no zstd support found: install Python 3.14+, or run: pip install zstandard')

def frame_ok(frame,want_dict):
    """True if a compressed file's header records its size (single segment) and has a dictionary iff wanted."""
    fhd=frame[4]
    return bool(fhd&0x20) and (fhd&3!=0)==bool(want_dict)
