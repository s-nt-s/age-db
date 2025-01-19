from typing import NamedTuple, Tuple


class Link(NamedTuple):
    href: str
    text: str


class IdTxt(NamedTuple):
    id: int
    txt: str


class CodTxt(NamedTuple):
    cod: str
    txt: str


class CodTxtAgg(NamedTuple):
    cod: str
    txt: str
    agg: Tuple[str, ...]


class IdTxtFk(NamedTuple):
    id: int
    txt: str
    fk: int
