# -*- coding: utf-8 -*-
"""
Debug: comparar slicing por bytes vs. por caracteres no data area.
Se o ISO usa byte offsets no directory, precisamos fatiar bytes, não chars.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\kauen\Downloads\teste_grande.iso', 'rb') as f:
    raw = f.read()

raw = raw.replace(b'\r\n', b'').replace(b'\r', b'').replace(b'\n', b'')

# Achar um registro que tenha muitos caracteres multi-byte antes dos campos problemáticos
# Vamos iterar e achar o PRIMEIRO registro onde byte-slice != char-slice
pos = 0
rec_num = 0
mismatches = 0

while pos < len(raw) and rec_num < 500:
    if pos + 24 > len(raw):
        break
    leader = raw[pos:pos+24]
    try:
        rec_len = int(leader[0:5])
        base_addr = int(leader[12:17])
    except ValueError:
        pos += 1
        continue

    if pos + rec_len > len(raw):
        break

    record_bytes = raw[pos:pos+rec_len]
    data_bytes = record_bytes[base_addr:]
    data_str = data_bytes.decode('utf-8', errors='replace')

    # Parse directory
    dir_bytes = record_bytes[24:base_addr]
    dir_str = dir_bytes.decode('ascii', errors='replace')
    tags = []
    i = 0
    while i + 12 <= len(dir_str):
        tag = dir_str[i:i+3]
        try:
            flen = int(dir_str[i+3:i+7])
            fpos = int(dir_str[i+7:i+12])
        except ValueError:
            break
        tags.append((tag, flen, fpos))
        i += 12

    # Compare byte-slice vs char-slice for each field
    has_mismatch = False
    for tag, flen, fpos in tags:
        # Method A: char-slice (current parser - potentially wrong)
        val_char = data_str[fpos:fpos+flen]
        # Method B: byte-slice then decode (correct for ISO 2709)
        val_byte = data_bytes[fpos:fpos+flen].decode('utf-8', errors='replace')

        if val_char != val_byte:
            if not has_mismatch:
                print(f"\n=== Record {rec_num} (pos={pos}, len={rec_len}, base={base_addr}) ===")
                print(f"  Data area: {len(data_bytes)} bytes, {len(data_str)} chars")
                has_mismatch = True

            print(f"  [{tag}] pos={fpos} len={flen}")
            print(f"    CHAR: {repr(val_char[:60])}")
            print(f"    BYTE: {repr(val_byte[:60])}")

    if has_mismatch:
        mismatches += 1
        if mismatches >= 5:
            print(f"\n... (mostrando apenas 5 primeiros mismatches)")
            break

    rec_num += 1
    pos += rec_len

print(f"\nTotal records checked: {rec_num}")
print(f"Records with mismatch: {mismatches}")
if mismatches == 0:
    print("NENHUM mismatch nos primeiros 500 registros!")
    print("O problema pode estar em outro lugar...")
