def flag(code):
    OFFSET = 127462 - ord('A')
    code = code.upper()
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)


def unflag(msg):
    OFFSET = 127462 - ord('A')
    return chr(ord(msg[0]) - OFFSET) + chr(ord(msg[1]) - OFFSET)