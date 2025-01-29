
from datetime import date, datetime
from types import MappingProxyType
import hashlib
import re
from spellchecker import SpellChecker
from functools import cache

ESP = SpellChecker(language="es", distance=1)
RM_TILDE = str.maketrans('áéíóúÁÉÍÓÚ', 'aeiouAEIOU')


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
    if hasattr(obj, '_asdict'):
        obj = obj._asdict()
    if isinstance(obj, dict):
        return {key: json_serial(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return list(map(json_serial, obj))
    return obj


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


def to_title(s: str):
    def _to_tt(w: str):
        if len(w) < 2:
            return w
        if w in ("los", "las", "del", "el", "la", "de"):
            return w
        return w.title()
    if not isinstance(s, str):
        return s
    s = " ".join(map(_to_tt, s.lower().split()))
    s = re.sub(r", \w+$", lambda x: x.group().title(), s)
    s = s[0].upper() + s[1:]
    s = to_fix(s)
    return s


def copy_case(a: str, b: str):
    if a.upper() == a:
        return b.upper()
    if a.lower() == a:
        return b.lower()
    if a.title() == a:
        return b.title()
    if a.capitalize() == a:
        return b.capitalize()
    if len(a) != len(b):
        raise ValueError(f"Las longitudes deben coincidir, len(a)={len(a)} != len(b)={len(b)}")
    return ''.join(
        y.upper() if x.isupper() else y.lower()
        for x, y in zip(a, b)
    )


def to_capitalize(s: str):
    if not isinstance(s, str):
        return s
    s = s.capitalize()
    s = re.sub(r", \w+$", lambda x: x.group().title(), s)
    s = to_fix(s)
    return s


@cache
def fix_tilde(s: str):
    if not re.match(r"^[a-zA-Z]+$", s) or len(s) < 3:
        return s
    lw = s.lower()
    for ok in (ESP.candidates(lw) or ()):
        if ok.translate(RM_TILDE) == lw:
            return copy_case(s, ok)
    return s


def to_fix(s: str):
    s = "".join(map(fix_tilde, re.split(r"\b", s)))
    for k, v in ({
        "meritos": "méritos",
        "informatica": "informática",
        "tecnicos": "técnicos",
        "maritimos": "marítimos",
        "titulacion": "titulación",
        "tecnico": "técnico",
        "tecnicos": "técnicos",
        "telegrafos": "telégrafos",
        "biologicas": "biológicas",
        "fisicas": "físicas",
        "geologicas": "geológicas",
        "matematicas": "matemáticas",
        "quimicas": "químicas",
        "economicas": "económicas",
        "aeronautico": "aeronáutico",
        "agronomo": "agrónomo",
        "codigos": "códigos",
        "segun": "según",
        "idoneos": "idóneos",
        "caracteristicas": "características",
        "bibliograficos": "bibliográficos",
        "tecnicas": "técnicas",
        "microinformatica": "microinformática",
        "programacion": "programación",
        "intrumentaciones": "instrumentaciones",
        "radioelectricas": "radioeléctricas",
        "semiticas": "semíticas",
        "dias": "días",
        "microfilmacion": "microfilmación",
        "planificacion": "planificación",
        "bibliograficos": "bibliográficos",
        "estadisticos": "estadísticos",
        "podran": "podrán",
        "metodos": "métodos",
        "estadisticas": "estadísticas",
        "informaticos": "informáticos",
        "tecnologias": "tecnologías",
        "cominicaciones": "comunicaciones",
        "telecominicacion": "telecomunicación",
        "radioelectronica": "radioelectrónica",
        "radioelectronico": "radioelectrónico"
    }).items():
        s = re.sub(
            r"\b"+k+r"\b",
            lambda x: copy_case(x.group(), v),
            s,
            flags=re.IGNORECASE
        )
    s = re.sub(r"\bn[,\. ]?\d+\b(:?$| )", lambda x: re.sub(r"n[,\. ]?", "N", x.group()), s)
    for w in (
        'España',
        'Europa',
        'USA',
        'INAP',
        'Cataluña',
        'INSS',
        'Muface',
        'Formentera',
        'SOIVRE',
        'CSIC',
        'Andalucia',
        'Aragón',
        'Asturias',
        'Illes Balears',
        'Canarias',
        'Cantabria',
        'Castilla la Mancha'
        'Castilla y León',
        'Extremadura',
        'Galicia',
        'La Rioja',
        'Madrid',
        'Murcia',
        'Navarra',
        'País Vasco',
        'Ceuta',
        'Melilla',
        'Baleares',
        'FEGA',
        'OEPM',
        'CIEMAT',
        'ISCIII',
        'ISM',
        'UIMP'
    ):
        s = re.sub(r"\b"+w+r"\b", w, s, flags=re.IGNORECASE)
    return s
