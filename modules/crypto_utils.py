def get_bundled_key():
    """
    Returns the unscrambled GROQ API Key.
    The key is XOR obfuscated to prevent simple string extraction.
    """
    obfuscated_bytes = [37, 49, 41, 29, 114, 122, 56, 8, 10, 21, 15, 58, 38, 1, 27, 4, 36, 20, 59, 1, 36, 4, 45, 43, 21, 5, 38, 59, 32, 113, 4, 27, 53, 116, 118, 50, 5, 46, 38, 20, 55, 23, 4, 23, 15, 53, 114, 115, 17, 12, 52, 3, 54, 26, 9, 27]
    xor_key = 0x42
    return "".join(chr(b ^ xor_key) for b in obfuscated_bytes)
