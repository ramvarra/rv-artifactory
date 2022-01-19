import hashlib

def md5_checksum(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

# Ack: https://github.com/devopshq/artifactory/blob/master/artifactory.py
def escape_chars(s: str) -> str:
    """
    Performs character escaping of comma, pipe and equals characters
    """
    assert isinstance(s, str), f"bad non str value in property '{s}'"
    return "".join(["\\" + ch if ch in "=|," else ch for ch in s])

def encode_properties(parameters: dict) -> str:
    """
    Performs encoding of url parameters from dictionary to a string. It does
    not escape backslash because it is not needed.
    See: http://www.jfrog.com/confluence/display/RTF/Artifactory+REST+API#ArtifactoryRESTAPI-SetItemProperties
    """
    result = []

    for key, value in parameters.items():
        if isinstance(value, (list, tuple)):
            value = ",".join([escape_chars(x) for x in value])
        else:
            value = escape_chars(value)

        result.append("=".join((key, value)))

    return ";".join(result)