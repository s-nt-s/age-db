import json
import re
from functools import cached_property, cache
from io import StringIO
from os.path import isfile
from typing import Tuple, Union, NamedTuple, Dict
from pypdf import PdfReader
from datetime import datetime
from types import MappingProxyType
from typing import Mapping
from .util import to_hash
from .tp import Link

import tabula
import urllib3

from .filemanager import FM
from .util import tmap, to_num, json_serial
from .web import Web

urllib3.disable_warnings()

re_cellnb = re.compile(r'\s([\d\.,]+)\s')
re_sp = re.compile(r"\s+")


def parseTb(table) -> Tuple[Tuple[Union[str, int, float], ...]]:
    if table is None:
        return tuple()
    s = StringIO()
    sep = '\t'
    table.to_csv(s, index=False, header=False, sep=sep)
    s = s.getvalue()
    s = s.strip()
    rows = []
    for r in s.split("\n"):
        r = re_cellnb.sub(lambda m: sep + m.group() + sep, r)
        r = r.strip()
        row = []
        for c in re.split(r"\s*\t\s*", r):
            c = to_num(c, safe=True)
            if isinstance(c, str):
                slp = tmap(lambda x: to_num(x, safe=True), re.split(r"\s+", c))
                if not any([x for x in slp if isinstance(x, str)]):
                    row.extend(slp)
                    continue
            row.append(c)
        rows.append(tuple(row))
    return tuple(rows)


class RetribucionError(ValueError):
    def __init__(self, link: Link, msg: str):
        super().__init__(link.href+" "+msg)


class SueldoTrienio(NamedTuple):
    sueldo: float
    trienio: float


class TablaSueldo(NamedTuple):
    base: SueldoTrienio
    extra: SueldoTrienio


class RetribucionesFinder:
    ROOT = 'https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/CostesPersonal/EstadisticasInformes/Paginas/RetribucionesPersonalFuncionario.aspx'

    @cached_property
    def pdfs(self):
        w = Web(verify=False)
        retribucion: Dict[str, Link] = {}
        w.get(RetribucionesFinder.ROOT)
        for a in w.soup.select("a[href]"):
            txt = re_sp.sub(" ", a.get_text()).strip()
            if re.match(r"^Retribuciones (del )?personal funcionario.*20\d+.*", txt):
                yr = tuple(map(int, re.findall(r"20\d+", txt)))
                if yr[0] > 2000:
                    url = a.attrs["href"]
                    yr = int(yr[0])
                    if yr not in retribucion:
                        retribucion[yr] = Link(href=url, text=txt)
        return retribucion

    def get(self, year=None):
        if len(self.pdfs) == 0:
            return None
        if year is None:
            year = max(self.pdfs.keys())
        if year not in self.pdfs:
            return None
        link = self.pdfs[year]
        return Retribuciones(
            anio=year,
            link=link,
            via=RetribucionesFinder.ROOT
        )


class Retribuciones:
    sueldo: Mapping[str, TablaSueldo]

    def __init__(self, anio: int, link: Link, via: str):
        self.__anio = anio
        self.__link = link
        self.__via = via
        self.__file = FM.resolve_path(f"dwn/retribucion_{anio}_{to_hash(link.href)}.pdf")
        if not isfile(self.__file):
            r = Web().s.get(link.href, verify=False)
            FM.dump(self.__file, r.content)

    @property
    def anio(self):
        return self.__anio

    @property
    def link(self):
        return self.__link

    @property
    def via(self):
        return self.__via

    @cached_property
    def fecha(self):
        metadata = PdfReader(self.__file).metadata
        modDate = metadata.get("/ModDate", None)
        if modDate is None:
            return None
        modDate = modDate[2:] 
        return datetime.strptime(modDate[:14], "%Y%m%d%H%M%S")

    @cached_property
    def destino(self):
        _, tableC = self.__get_tables()
        destino: Dict[int, float] = {}
        for row in tableC:
            if row[0] is None or not isinstance(row[0], int):
                continue
            row = [r for i, r in enumerate(row) if i % 2 == 0]
            row = iter(row)
            nivel = int(next(row))
            compd = float(next(row))
            destino[nivel] = compd
        return MappingProxyType(destino)

    @cached_property
    def sueldo(self):
        tableS, _ = self.__get_tables()

        data = dict()
        grupos = ("A1", "A2", "B", "C1", "C2", "E")
        for g in grupos:
            data[g] = dict()

        for row in tableS:
            if not (len(row) > 2 and isinstance(row[0], str) and isinstance(row[1], (int, float))):
                continue
            txt = row[0].replace(" ", '')
            sld = tuple(r for i, r in enumerate(row[1:]) if i % 2 == 0)
            tri = tuple(r for i, r in enumerate(row[1:]) if i % 2 == 1)
            key = None
            if txt.startswith("ANUAL"):
                key = "base" 
            elif txt.startswith("PAGAEXTRAJUNIO"):
                key = "junio"
            elif txt.startswith("PAGAEXTRADICIEMBRE"):
                key = "diciembre"
            if key is None:
                continue
            for i, g in enumerate(grupos):
                data[g][key] = SueldoTrienio(
                    sueldo=sld[i],
                    trienio=tri[i]
                )
        rnt: Dict[str, TablaSueldo] = {}
        for g, v in data.items():
            if v['junio'] != v['diciembre']:
                raise RetribucionError(self.__link, "junio != diciembre")
            v['extra'] = v['junio']
            del v['junio']
            del v['diciembre']
            ts = TablaSueldo(**v)
            rnt[g] = ts

        return MappingProxyType(rnt)

    @cache
    def __get_tables(self):
        tableC = None
        tableS = None
        for t in tabula.read_pdf(self.__file, pages=1, multiple_tables=True):
            if 'COMPLEMENTO DE DESTINO' in t.columns:
                tableC = t
            elif 'A2' in t.columns and 'A2' in t.columns and 'C1' in t.columns:
                tableS = t
        tableS = parseTb(tableS)
        tableC = parseTb(tableC)
        for index, row in enumerate(tableS):
            if not tableC and row[0] == 'COMPLEMENTO DE DESTINO':
                tableC = tableS[index:]
                tableS = tableS[:index]
                break
        return tableS, tableC

    def _asdict(self):
        return dict(
            anio=self.anio,
            fuente=self.link.href,
            text=self.link.text,
            via=self.via,
            fecha=self.fecha,
            sueldo=self.sueldo,
            destino=self.destino
        )


if __name__ == '__main__':
    r = RetribucionesFinder()
    r = r.get()

    print(json.dumps(r._asdict(), indent=2, default=json_serial))
