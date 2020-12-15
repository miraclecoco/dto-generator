def check_key(d: dict, key: str, desc: str = None) -> None:
    if desc is None:
        desc = key

    if key not in d:
        raise KeyError("'{0}' is missing".format(desc))
