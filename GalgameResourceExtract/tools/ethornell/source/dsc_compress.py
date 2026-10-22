import struct
import sys
from collections import Counter
import heapq

"""
DSC (AKA extensionless file) Compressor for BGI/Ethornell

This was made first replicating GARbro's decompression function (as seen in dsc_decompress.py), then reversing the process for compression.

Available here: https://github.com/morkt/GARbro/blob/master/ArcFormats/Ethornell/ArcBGI.cs
"""

def update_key(key, magic):
    """BGI PRNG for encryption"""
    v0 = 20021 * (key & 0xFFFF)
    v1 = magic | (key >> 16)
    v1 = v1 * 20021 + key * 346
    v1 = (v1 + (v0 >> 16)) & 0xFFFF
    new_key = (v1 << 16) + (v0 & 0xFFFF) + 1
    return new_key, v1 & 0xFF


def lz77_compress(data):
    """
    LZ77 compression:
    - Literals: 0-255
    - Backreferences: 256-511 (code = 256 + length - 2)
    - Max length: 257 bytes
    - Max offset: 4097 bytes
    """
    symbols = []
    pos = 0
    
    while pos < len(data):
        best_length = 0
        best_offset = 0
        
        search_start = max(0, pos - 4097)
        
        for offset in range(pos - search_start, 1, -1):
            if offset < 2:
                continue
            
            match_pos = pos - offset
            length = 0
            
            while (length < 257 and 
                   pos + length < len(data) and 
                   data[match_pos + length] == data[pos + length]):
                length += 1
            
            if length > best_length:
                best_length = length
                best_offset = offset
        
        if best_length >= 3:
            code = 256 + (best_length - 2)
            symbols.append((code, best_offset))
            pos += best_length
        else:
            symbols.append((data[pos], None))
            pos += 1
    
    return symbols


def build_huffman_tree(symbols):
    """Build Huffman tree and calculate code depths"""
    freq = Counter()
    for symbol, _ in symbols:
        freq[symbol] += 1
    
    heap = []
    counter = 0
    for symbol, count in freq.items():
        heapq.heappush(heap, (count, counter, symbol, None, None))
        counter += 1
    
    while len(heap) > 1:
        freq1, id1, sym1, left1, right1 = heapq.heappop(heap)
        freq2, id2, sym2, left2, right2 = heapq.heappop(heap)
        parent = (freq1 + freq2, counter, None, 
                 (freq1, id1, sym1, left1, right1), 
                 (freq2, id2, sym2, left2, right2))
        heapq.heappush(heap, parent)
        counter += 1
    
    depths = [0] * 512
    
    def calculate_depths(node, depth=0):
        freq, node_id, symbol, left, right = node
        if symbol is not None:
            depths[symbol] = depth if depth > 0 else 1
        else:
            if left:
                calculate_depths(left, depth + 1)
            if right:
                calculate_depths(right, depth + 1)
    
    if heap:
        calculate_depths(heap[0])
    
    for symbol in freq.keys():
        if depths[symbol] == 0:
            depths[symbol] = 1
        elif depths[symbol] > 255:
            depths[symbol] = 255
    
    return depths


def assign_canonical_codes(depths):
    """Assign canonical Huffman codes from depths"""
    symbol_depths = [(i, depths[i]) for i in range(512) if depths[i] > 0]
    symbol_depths.sort(key=lambda x: (x[1], x[0]))
    
    codes = {}
    code = 0
    prev_depth = 0
    
    for symbol, depth in symbol_depths:
        if depth > prev_depth:
            code <<= (depth - prev_depth)
            prev_depth = depth
        codes[symbol] = (code, depth)
        code += 1
    
    return codes


def write_dsc_file(output_path, input_data, key):
    """Compress and write DSC file"""
    magic = 0x53440000  # "DS" << 16
    
    print(f"Compressing {len(input_data)} bytes...")
    symbols = lz77_compress(input_data)
    print(f"  LZ77: {len(symbols)} symbols")
    
    depths = build_huffman_tree(symbols)
    non_zero = sum(1 for d in depths if d > 0)
    print(f"  Huffman: {non_zero} codes")
    
    codes = assign_canonical_codes(depths)
    
    output = bytearray()
    
    # Header
    output.extend(b'DSC FORMAT 1.00\x00')
    output.extend(struct.pack('<I', key))
    output.extend(struct.pack('<I', len(input_data)))
    output.extend(struct.pack('<I', len(symbols)))
    output.extend(b'\x00' * 4)
    
    # Encrypted Huffman tree
    temp_key = key
    for i in range(512):
        temp_key, enc_byte = update_key(temp_key, magic)
        encrypted_depth = (depths[i] + enc_byte) & 0xFF
        output.append(encrypted_depth)
    
    # Compressed data (MSB first)
    bit_buffer = 0
    bits_in_buffer = 0
    
    for symbol, offset in symbols:
        code, code_length = codes[symbol]
        
        # Write Huffman code
        for i in range(code_length):
            bit = (code >> (code_length - 1 - i)) & 1
            bit_buffer = (bit_buffer << 1) | bit
            bits_in_buffer += 1
            
            if bits_in_buffer == 8:
                output.append(bit_buffer)
                bit_buffer = 0
                bits_in_buffer = 0
        
        # Write backreference offset
        if symbol >= 256 and offset is not None:
            offset_bits = offset - 2
            for i in range(12):
                bit = (offset_bits >> (11 - i)) & 1
                bit_buffer = (bit_buffer << 1) | bit
                bits_in_buffer += 1
                
                if bits_in_buffer == 8:
                    output.append(bit_buffer)
                    bit_buffer = 0
                    bits_in_buffer = 0
    
    if bits_in_buffer > 0:
        bit_buffer <<= (8 - bits_in_buffer)
        output.append(bit_buffer)
    
    with open(output_path, 'wb') as f:
        f.write(output)
    
    print(f"Written {len(output)} bytes to {output_path}")
    print(f"Compression ratio: {(len(output) / len(input_data) * 100 if input_data else 0):.1f}%")


def main():
    if len(sys.argv) < 4:
        print("Usage: python dsc_compress.py <input_file> <output_dsc> <key_hex>")
        print("Example: python dsc_compress.py 01_epilogue1 01_epilogue1_compressed 02207D06")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    key = int(sys.argv[3], 16)
    
    with open(input_file, 'rb') as f:
        data = f.read()
    
    print(f"Input: {input_file}")
    print(f"Key: 0x{key:08X}")
    
    write_dsc_file(output_file, data, key)


if __name__ == "__main__":
    main()
