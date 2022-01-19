import hashlib

def md5_checksum(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()
