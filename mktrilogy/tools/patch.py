"""Guarded patches.

A patch names the instructions it expects at its site (as disassembly text), checks them, then
writes our replacement bytes. A ROM that does not match stops the build with a clear message.
"""
from . import d65
from .hirom import Rom


class PatchError(Exception):
    pass


class Patch:
    def __init__(self, name, addr, expect, new, m16=True, x16=True, why=''):
        self.name, self.addr, self.expect, self.new = name, addr, list(expect), bytes(new)
        self.m16, self.x16, self.why = m16, x16, why

    def check(self, rom):
        got = d65.text_at(rom, self.addr, len(self.expect), self.m16, self.x16)
        if got != self.expect:
            raise PatchError('%s: expected %s at $%06X, found %s'
                             % (self.name, self.expect, self.addr, got))

    def apply(self, data, mapper):
        rom = Rom(data, mapper)
        self.check(rom)
        o = rom.off(self.addr)
        data[o:o + len(self.new)] = self.new
        return o


def expect_at(rom, addr, expect, name, m16=True, x16=True):
    """A guard with no write, for context the patch relies on."""
    got = d65.text_at(rom, addr, len(expect), m16, x16)
    if got != list(expect):
        raise PatchError('%s: expected %s at $%06X, found %s' % (name, list(expect), addr, got))
