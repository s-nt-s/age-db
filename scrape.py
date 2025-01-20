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
        db.insert("NIVEL", id=nivel, complemento_destino=cd)

    p_txt = tuple(sorted(set(r.txt for r in rpt.puestos)))
    for i, txt in enumerate(p_txt):
        db.insert("CARGO", id=i+1, txt=to_capitalize(txt))

    for row in map(rpt.complete, rpt.puestos):
        obj = row._asdict()
        obj["localidad"] = lcd[(row.localidad, row.provincia)]
        obj["cargo"] = p_txt.index(row.txt)+1
        db.insert("PUESTO", **obj)
        for o in row.observaciones:
            db.insert("PUESTO_OBSERVACION", puesto=row.id, observacion=o)
        for c in row.cuerpos:
            db.insert("PUESTO_CUERPO", puesto=row.id, cuerpo=c)
        for t in row.titulaciones:
            db.insert("PUESTO_TITULACION", puesto=row.id, titulacion=t)
        for g in row.grupos:
            db.insert("PUESTO_GRUPO", puesto=row.id, grupo=g)

    db.execute(FM.load("sql/end.sql"))
