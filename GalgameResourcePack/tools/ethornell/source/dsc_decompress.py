import struct
import sys
import os

"""
DSC (AKA extensionless file) Decompressor for BGI/Ethornell

This is a replica of GARbro's decompression function, implemented in Python.

Available here: https://github.com/morkt/GARbro/blob/master/ArcFormats/Ethornell/ArcBGI.cs
"""

class DscDecoder:
    def __init__(self, data):
        if len(data) < 0x220 or data[:16] != b"DSC FORMAT 1.00\0":
            raise ValueError("Invalid DSC stream")
        # Read header
        self.key = struct.unpack('<I', data[16:20])[0]
        self.original_size = struct.unpack('<I', data[20:24])[0]
        self.dec_count = struct.unpack('<I', data[24:28])[0]
        
        # Magic from "DS"
        self.magic = struct.unpack('<H', data[0:2])[0] << 16
        
        # Decrypt Huffman tree depths
        self.depths = bytearray(512)
        temp_key = self.key
        for i in range(512):
            temp_key, dec_byte = self.update_key(temp_key)
            encrypted_depth = data[0x20 + i]
            self.depths[i] = (encrypted_depth - dec_byte) & 0xFF
        
        # Build Huffman tree
        self.tree = self.create_huffman_tree()
        
        # Compressed data starts at 0x220
        self.compressed_data = data[0x220:]
        self.byte_pos = 0
        self.current_byte = self.compressed_data[0] if self.compressed_data else 0
        self.bits_left = 8
    
    def update_key(self, key):
        """BGI PRNG for decryption"""
        v0 = 20021 * (key & 0xFFFF)
        v1 = self.magic | (key >> 16)
        v1 = v1 * 20021 + key * 346
        v1 = (v1 + (v0 >> 16)) & 0xFFFF
        new_key = (v1 << 16) + (v0 & 0xFFFF) + 1
        return new_key, v1 & 0xFF
    
    def get_next_bit(self):
        """Read one bit (MSB first)"""
        if not self.compressed_data:
            raise ValueError("Truncated DSC bitstream")
        if self.bits_left == 0:
            self.byte_pos += 1
            if self.byte_pos < len(self.compressed_data):
                self.current_byte = self.compressed_data[self.byte_pos]
            else:
                raise ValueError("Truncated DSC bitstream")
            self.bits_left = 8
        
        bit = (self.current_byte >> 7) & 1
        self.current_byte = (self.current_byte << 1) & 0xFF
        self.bits_left -= 1
        return bit
    
    def get_bits(self, count):
        """Read multiple bits (MSB first)"""
        result = 0
        for _ in range(count):
            result = (result << 1) | self.get_next_bit()
        return result
    
    def create_huffman_tree(self):
        """Build Huffman tree using GARbro's algorithm"""
        root = [None, None]
        code = 0
        previous = 0
        for depth, symbol in sorted((depth, symbol) for symbol, depth in enumerate(self.depths) if depth):
            code <<= depth - previous
            previous = depth
            if code >= (1 << depth):
                raise ValueError("Oversubscribed DSC Huffman tree")
            node = root
            for shift in range(depth - 1, -1, -1):
                bit = (code >> shift) & 1
                if shift == 0:
                    if node[bit] is not None:
                        raise ValueError("Invalid DSC Huffman tree")
                    node[bit] = symbol
                else:
                    if node[bit] is None:
                        node[bit] = [None, None]
                    if not isinstance(node[bit], list):
                        raise ValueError("Invalid DSC Huffman prefix")
                    node = node[bit]
            code += 1
        return root

    def huffman_decompress(self):
        """Decompress using Huffman + LZ77"""
        output = bytearray()
        
        for _ in range(self.dec_count):
            # Traverse tree to get symbol
            node = self.tree
            while isinstance(node, list):
                node = node[self.get_next_bit()]
                if node is None:
                    raise ValueError("Invalid DSC Huffman code")
            symbol = node

            if symbol < 256:
                # Literal
                output.append(symbol)
            else:
                # Backreference
                length = symbol - 256 + 2
                offset_bits = self.get_bits(12)
                offset = offset_bits + 2
                
                if offset > len(output):
                    raise ValueError("DSC backreference outside output")
                copy_pos = len(output) - offset
                for _ in range(length):
                    output.append(output[copy_pos])
                    copy_pos += 1
        
            if len(output) > self.original_size:
                raise ValueError("DSC output exceeds declared size")
        if len(output) != self.original_size:
            raise ValueError("DSC output size mismatch")
        return bytes(output)


def decompress_dsc(input_path, output_path):
    """Decompress DSC file"""
    with open(input_path, 'rb') as f:
        data = f.read()
    
    decoder = DscDecoder(data)
    decompressed = decoder.huffman_decompress()
    
    with open(output_path, 'wb') as f:
        f.write(decompressed)
    
    print(f"Decompressed {len(data)} bytes -> {len(decompressed)} bytes")
    print(f"Output: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python dsc_decompress.py <input> [output_file_or_folder]")
        print("Example: python dsc_decompress.py 01_Epilogue1 01_Epilogue1_decompressed")
        print("         python dsc_decompress.py 01_Epilogue1 decompressed/")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_arg = sys.argv[2]
        # Check if output_arg is a directory
        if os.path.isdir(output_arg) or output_arg.endswith(('/','\\')) or output_arg.endswith(('/', '\\')):
            # It's a directory - preserve filename
            os.makedirs(output_arg, exist_ok=True)
            filename = os.path.basename(input_file)
            output_file = os.path.join(output_arg, filename)
        else:
            # It's a file path
            output_file = output_arg
    else:
        output_file = "decompressed.txt"
    
    decompress_dsc(input_file, output_file)


if __name__ == "__main__":
    main()
