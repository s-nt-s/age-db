import logging

from .web import Web, get_text
import re
from .tp import Link
from functools import cached_property
from typing import Dict
from types import MappingProxyType
from . boe import BOE

logger = logging.getLogger(__name__)


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


class MufaceError(ValueError):
    def __init__(self, link: Link, msg: str):
        super().__init__(link.href+" "+msg)


class Muface:
    ROOT = "https://www.muface.es/muface_Home/mutualistas/cotizacion/Regimen-de-Cotizaciones.html"

    def __init__(self):
        self.__soup = Web().get(Muface.ROOT)
        self.__link = Link(Muface.ROOT, get_text(self.__soup.find("title")))

    @property
    def via(self):
        return self.__link.href

    @property
    def link(self):
        return self.__link

    @cached_property
    def cotizacion_general(self):
        data: Dict[str, float] = {}
        li = self.__findMutualistas()
        ul = li.find_parent("ul")
        table = ul.find_next_sibling("table")
        for tr in table.select("tbody tr"):
            tds = tuple(map(get_text, tr.select("td")))
            g = tds[0]
            g = g.upper()
            g = g.split()[0]
            if len(g) < 3 and g[0] in ("A", "B", "C", "E"):
                data[g] = to_num(tds[-1])
        return MappingProxyType(data)

    def __findMutualistas(self):
        tag = "strong"
        txt = "Mutualistas obligatorios (cuota mensual):"
        for s in self.__soup.select(tag):
            if txt in str(s):
                return s.find_parent("li")
        raise MufaceError(self.__link, f"Not found <{tag}>{txt}</{tag}")

    @cached_property
    def boe(self):
        re_boe = re.compile(r".*\bboe\.es/.*(BOE-[\w\-]+)")
        for a in self.__soup.select("div.mod_content_gen a"):
            m = re_boe.search(a.attrs["href"])
            if m is None:
                continue
            return m.groups()[0]

    @cached_property
    def fecha(self):
        return BOE(self.boe).modificado


if __name__ == "__main__":
    print(Muface().cotizacion_general)
