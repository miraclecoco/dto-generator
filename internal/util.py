

def upper_first(s: str):
    return s[0:1].upper() + s[1:]


def check_key(d: dict, key: str, desc: str = None) -> None:
    if desc is None:
        desc = key

    if key not in d:
        raise KeyError("'{0}' is missing".format(desc))
