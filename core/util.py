
from datetime import date, datetime
from types import MappingProxyType
import hashlib
import re

def to_hash(s: str):
    hash_obj = hashlib.sha256(s.encode("utf-8"))
    return hash_obj.hexdigest()


def tmap(f, a):
    return tuple(map(f, a))


def to_num(s, safe=False):
    if s is None:
        return None
    if safe is True:
        try:
            return to_num(s)
        except ValueError:
            return s
    if isinstance(s, str):
        s = s.replace("€", "")
        s = s.replace(".", "")
        s = s.replace(",", ".")
        s = float(s)
    if int(s) == s:
        s = int(s)
    return s

def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M")
    if isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, MappingProxyType):
        obj = dict(obj)
    if  hasattr(obj, '_asdict'):
        obj = obj._asdict()
    if isinstance(obj, dict):
        return {key: json_serial(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return list(map(json_serial, obj))
    return obj

def to_title(s: str):
    def _to_tt(w: str):
        if len(w)<2:
            return w
        if w in ("los", "las", "del", "el", "la", "de"):
            return w
        return w.title()
    if not isinstance(s, str):
        return s
    s = " ".join(map(_to_tt, s.lower().split()))
    s = re.sub(r", \w+$", lambda x: x.group().title(), s)
    return s


def to_capitalize(s: str):
    if not isinstance(s, str):
        return s
    s = s.lower()
    s = s[0].upper() + s[1:].lower()
    for w in ('España', 'Europa'):
        s = re.sub(r"\b"+w+r"\b", w, s, flags=re.IGNORECASE)
    s = re.sub(r", \w+$", lambda x: x.group().title(), s)
    return s



def countDec(f: float):
    if f == int(f):
        return 0
    return len(str(f).split(",")[-1])


def myrange(begin: float, end: float, step: float = None):
    if step is None:
        step = 1
    if begin == int(begin) and end == int(end) and (step is None or int(step) == step):
        yield from range(begin, end+step, step)
    factor = 10 ** max(map(countDec, [begin, end, 1 if step is None else step]))
    for i in range(int(begin*factor), int(end*factor)+step, step):
        yield i/factor