"""Input ROM identities. The build only accepts these exact dumps."""
import hashlib

KNOWN = {
    'umk3': ('09c094ca1114bcb6d5917e989686ca79b96cf9ea', 0x400000, 'Ultimate Mortal Kombat 3 (USA)'),
    'mk3': ('58e4e1259a86faaadbc982176e569cb2038dbac5', 0x400000, 'Mortal Kombat 3 (USA)'),
    'mk2': ('f6aa5291759e982ea249c4b76f729ca2f4ab1cf4', 0x300000, 'Mortal Kombat II (USA)'),
}


class RomError(Exception):
    pass


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def load(name, path):
    """Read a ROM, strip a 512-byte copier header if present, and check its SHA-1."""
    want_sha, want_size, title = KNOWN[name]
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) == want_size + 512:
        data = data[512:]
    got = sha1(data)
    if got != want_sha:
        raise RomError('%s: expected the %s dump (SHA-1 %s), got SHA-1 %s'
                       % (path, title, want_sha, got))
    return data
