from core.dblite import DBLite, dict_factory, gW
import argparse
from core.filemanager import FM
from typing import Tuple, Union, Dict, NamedTuple


parser = argparse.ArgumentParser(
    description='Reescribe README.md',
)
parser.add_argument(
    '--db', type=str, default="db/age.sqlite"
)
parser.add_argument(
    '--md', type=str, default="README.md"
)

ARG = parser.parse_args()


def get_vals(db: DBLite, p: int, rel: str, txt_table: str = None) -> Union[Dict, Tuple]:
    rel_table, rel_col = rel.split(".")
    ids = db.to_tuple(f"select {rel_col} from {rel_table} where puesto = {p} order by {rel_col}")
    if txt_table is None:
        return ids
    if len(ids) == 0:
        return dict()
    return db.to_dict(f"select id, txt from {txt_table} where id {gW(ids)} order by id")


def get_id_txt(db: DBLite, table: str, id) -> str:
    return db.one(f"select id || ' ' || txt from {table} where id = ?", id),


class Puesto(NamedTuple):
    id: int
    observacion: Dict
    cuerpo: Dict
    titulacion: Dict
    grupo: Dict
    cargo: str
    nivel: int
    especifico: float
    vacante: bool
    localidad: str
    unidad: str
    tipo: str
    provision: str
    administracion: str
    formacion: str


SQL_PUESTO = '''
    select
        p.id,
        ca.txt cargo,
        (un.id || ' ' || un.txt) unidad,
        lc.txt localidad,
        p.nivel,
        p.especifico,
        ti.txt tipo,
        pr.txt provision,
        ad.txt administracion,
        (fo.id || ' ' || fo.txt) formacion,
        p.vacante
    from
        PUESTO p
        LEFT JOIN
        CARGO ca on ca.id=p.cargo
        LEFT JOIN
        UNIDAD un on un.id=p.unidad
        LEFT JOIN
        LOCALIDAD lc on lc.id=p.localidad
        LEFT JOIN
        TIPO_PUESTO ti on ti.id=p.tipo
        LEFT JOIN
        PROVISION pr on pr.id=p.provision
        LEFT JOIN
        ADMINISTRACION ad on ad.id=p.administracion
        LEFT JOIN
        FORMACION fo on fo.id=p.formacion
'''

