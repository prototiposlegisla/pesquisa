import sys
with open(sys.argv[1], 'rb') as f:
    raw = f.read()
raw = raw.replace(b'\r\n', b'').replace(b'\r', b'').replace(b'\n', b'')
idx = raw.find(b'Lei n')
if idx >= 0:
    snippet = raw[idx:idx+20]
    print("Hex:", snippet.hex(' '))
    print("Latin-1:", snippet.decode('latin-1'))
    try:
        print("UTF-8:", snippet.decode('utf-8'))
    except:
        print("UTF-8: FAILED (not valid utf-8)")
