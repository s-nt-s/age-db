from core.dblite import DBLite
from core.filemanager import FM
from core.retribuciones import RetribucionesFinder
from core.rpt import RPTFinder
from core.muface import Muface
from core.util import to_title, to_capitalize
from typing import Dict, Tuple
import logging
import re

import argparse


parser = argparse.ArgumentParser(
    description='Reescribe README.md',
)
parser.add_argument(
    '--db', type=str, default="db/age.sqlite"
)

ARG = parser.parse_args()

open("build.log", "w").close()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S',
    handlers=[
        logging.FileHandler("build.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


with DBLite(ARG.db, reload=True) as db:
    db.execute(FM.load("sql/schema.sql"))
    mf = Muface()
    ret = RetribucionesFinder().get()
    rpt = RPTFinder().get()
    db.insert(
        "FUENTE",
        id="Muface",
        fuente=mf.link.href,
        via=mf.via,
        fecha=mf.fecha.date()
    )
    db.insert(
        "FUENTE",
        id="Retribuciones",
        fuente=ret.link.href,
        via=ret.via,
        fecha=ret.fecha.date()
    )
    db.insert(
        "FUENTE",
        id="RPT",
        fuente=rpt.link.href,
        via=rpt.via,
        fecha=rpt.fecha.date()
    )
    for row in rpt.pais:
        db.insert("PAIS", id=row.id, txt=to_title(row.txt))
    for row in rpt.provincias:
        db.insert("PROVINCIA", id=row.id, txt=to_title(row.txt), pais=row.fk)
    for i, row in enumerate(rpt.localidades):
        db.insert("LOCALIDAD", id=i+1, localidad=row.id, txt=to_title(row.txt), provincia=row.fk)
    for row in rpt.ministerios:
        db.insert("MINISTERIO", id=row.id, txt=to_capitalize(row.txt))
    for row in rpt.centros:
        db.insert("CENTRO", id=row.id, txt=to_capitalize(row.txt), ministerio=row.fk)

    lcd: Dict[Tuple[int, int], int] = dict()
    for i, l, p in db.select("select id, localidad, provincia from LOCALIDAD"):
        lcd[(l, p)] = i
    for row in rpt.unidades:
        l_id = lcd[(row.localidad, row.provincia)]
        db.insert("UNIDAD", id=row.id, txt=to_capitalize(row.txt), centro=row.centro, localidad=l_id)

    for table, arr in {
        "TIPO_PUESTO": rpt.tipos,
        "PROVISION": rpt.provision,
        "ADMINISTRACION": rpt.adminsitracion,
        "FORMACION": rpt.formaciones
    }.items():
        for row in arr:
            db.insert(table, id=row.cod, txt=to_capitalize(row.txt))

    for table, arr in {
        "CUERPO": rpt.cuerpos,
        "TITULACION": rpt.titulaciones,
        "OBSERVACION": rpt.observaciones,
    }.items():
        for row in arr:
            txt = to_capitalize(row.txt)
            if row.agg:
                txt = re.sub(
                    r"\b(" + "|".join(map(re.escape, row.agg)) + r")\b",
                    lambda x: x.group().upper(),
                    txt,
                    flags=re.IGNORECASE
                )
            db.insert(table, id=row.cod, txt=txt)

    grupos = tuple(sorted(
        set(rpt.grupos)
        .union(ret.sueldo.keys())
        .union(mf.cotizacion_general.keys())
    ))
    for grupo in grupos:
        sueldo = ret.sueldo[grupo]
        muface_cotizacion = mf.cotizacion_general[grupo]
        db.insert(
            "GRUPO",
            id=grupo,
            base=sueldo.base.sueldo,
            trienio=sueldo.base.trienio,
            extra_base=sueldo.extra.sueldo,
            extra_trienio=sueldo.extra.trienio,
            muface_cotizacion=muface_cotizacion
        )

    for nivel, cd in ret.destino.items():
        db.insert("NIVEL", id=nivel, destino=cd)

    cargos = tuple(sorted(set(to_capitalize(r.txt) for r in rpt.puestos)))
    for i, txt in enumerate(cargos):
        db.insert("CARGO", id=i+1, txt=txt)

    for row in map(rpt.complete, rpt.puestos):
        obj = row._asdict()
        obj["localidad"] = lcd[(row.localidad, row.provincia)]
        obj["cargo"] = cargos.index(to_capitalize(row.txt))+1
        db.insert("PUESTO", **obj)
        for o in row.observaciones:
            db.insert("PUESTO_OBSERVACION", puesto=row.id, observacion=o)
        for c in row.cuerpos:
            db.insert("PUESTO_CUERPO", puesto=row.id, cuerpo=c)
        for t in row.titulaciones:
            db.insert("PUESTO_TITULACION", puesto=row.id, titulacion=t)
        for g in row.grupos:
            db.insert("PUESTO_GRUPO", puesto=row.id, grupo=g)

    re_cup = re.compile(r"^EX\d+$")
    for id, txt in db.to_tuple("select id, txt from CUERPO"):
        if not re_cup.match(id):
            continue
        if not all(map(re_cup.match, re.split(r"[\s\+]+", txt))):
            continue
        logger.info(f"RM {id} = {txt}")
        db.execute("delete from PUESTO_CUERPO where cuerpo = ?", id)
        db.execute("delete from CUERPO where id = ?", id)
    re_cup = re.compile(r"^Agrupaci[oó]n de cuerpos [\(\)\d, yA-Z]+$")
    for id, txt in db.to_tuple("select id, txt from CUERPO"):
        if not re_cup.match(txt):
            continue
        logger.info(f"RM {id} = {txt}")
        db.execute("delete from PUESTO_CUERPO where cuerpo = ?", id)
        db.execute("delete from CUERPO where id = ?", id)
    re_tit = re.compile(r"^Incluye c[óo]digos \d[\d/A-Z ]+$")
    for id, txt in db.to_tuple("select id, txt from TITULACION"):
        if not re_tit.match(txt):
            continue
        logger.info(f"RM {id} = {txt}")
        db.execute("delete from PUESTO_TITULACION where titulacion = ?", id)
        db.execute("delete from TITULACION where id = ?", id)

    db.execute(FM.load("sql/end.sql"))
