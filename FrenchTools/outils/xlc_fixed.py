
import struct
from codec import decode, DecodeError


def parse_xlc(b):
    if b[:4] != b'xlce':
        return None

    n, do, es = struct.unpack_from('<III', b, 4)
    hend = 16 + n * es

    if hend >= len(b) or es < 4:
        return None

    cols = {}
    for c in range(0, es - 3, 4):
        cols[c] = [
            struct.unpack_from('<I', b, 16 + r * es + c)[0]
            for r in range(n)
        ]

    strcols = []

    for c, vals in cols.items():
        nz = set(v for v in vals if v)
        if not nz:
            continue

        valid = all(
            hend <= v < len(b)
            and (v == hend or b[v - 1] == 0 or b[v] == 0)
            for v in nz
        )

        if not valid:
            continue

        try:
            for v in nz:
                decode(b, v)
            strcols.append(c)
        except DecodeError:
            continue

    if not strcols:
        return None

    refs = sorted(set(
        v for c in strcols for v in cols[c] if v
    ))

    slots = []
    aliases = {}

    for v in refs:
        # An empty-string pointer may point directly
        # to the terminating zero of the preceding string.
        if (
            b[v] == 0
            and slots
            and v == slots[-1]['end'] - 1
        ):
            aliases[v] = slots[-1]['off']
            continue

        s, e = decode(b, v)
        slots.append(dict(off=v, text=s, end=e))

    if not slots:
        return None

    for a, c in zip(slots, slots[1:]):
        if c['off'] < a['end']:
            raise ValueError(
                'Unexpected overlapping XLC strings: '
                + hex(a['off']) + ' and ' + hex(c['off'])
            )
        a['gap'] = b[a['end']:c['off']]

    slots[-1]['gap'] = b''

    return dict(
        n=n,
        es=es,
        hend=hend,
        strcols=strcols,
        slots=slots,
        aliases=aliases,
        head=b[hEnd if False else hend:slots[0]['off']],
        tail=b[slots[-1]['end']:],
        cols=cols
    )


def build_xlc(b, info, encoded):
    if len(encoded) != len(info['slots']):
        raise ValueError('Incorrect number of encoded XLC strings')

    hend = info['hend']
    out = bytearray(b[:hend]) + info['head']

    newoff = {}
    alias_targets = {}

    for alias, target in info.get('aliases', {}).items():
        alias_targets.setdefault(target, []).append(alias)

    for s, enc in zip(info['slots'], encoded):
        newoff[s['off']] = len(out)
        out += enc

        # Empty-string pointers sharing this string's
        # original terminator must follow its new terminator.
        for alias in alias_targets.get(s['off'], []):
            newoff[alias] = len(out)

        out += b'\0' + s['gap']

    out += info['tail']

    for c in info['strcols']:
        for r, v in enumerate(info['cols'][c]):
            if v:
                if v not in newoff:
                    raise ValueError(
                        'Unmapped XLC pointer: ' + hex(v)
                    )
                struct.pack_into(
                    '<I', out,
                    16 + r * info['es'] + c,
                    newoff[v]
                )

    return bytes(out)
