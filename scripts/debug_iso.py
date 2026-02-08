import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\kauen\Downloads\teste_grande.iso', 'rb') as f:
    raw = f.read()

# Remove line breaks
raw = raw.replace(b'\r\n', b'').replace(b'\r', b'').replace(b'\n', b'')

# Parse first record
leader = raw[:24].decode('ascii')
rec_len = int(leader[0:5])
base_addr = int(leader[12:17])
print(f"Record length: {rec_len}, Base address: {base_addr}")

# Directory
dir_bytes = raw[24:base_addr].decode('ascii')
print(f"Directory ({len(dir_bytes)} bytes):")
i = 0
tags = []
while i + 12 <= len(dir_bytes):
    tag = dir_bytes[i:i+3]
    flen = int(dir_bytes[i+3:i+7])
    fpos = int(dir_bytes[i+7:i+12])
    tags.append((tag, flen, fpos))
    i += 12

for tag, flen, fpos in tags:
    print(f"  Tag {tag}: len={flen}, pos={fpos}")

# Data area
data = raw[base_addr:base_addr+rec_len-base_addr]
print(f"\nData area ({len(data)} bytes):")

for tag, flen, fpos in tags:
    field = data[fpos:fpos+flen].decode('utf-8', errors='replace')
    print(f"  [{tag}] ({fpos}:{fpos+flen}) = {repr(field[:80])}")
