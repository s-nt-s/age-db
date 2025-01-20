from core.dblite import DBLite
import argparse
from urllib.parse import urlparse
from core.filemanager import FM
from io import TextIOWrapper
from textwrap import dedent

parser = argparse.ArgumentParser(
    description='Reescribe README.md',
)
parser.add_argument(
    '--db', type=str, default="db/age.sqlite"
)

ARG = parser.parse_args()


def read(file: str):
    with open(file, "r") as f:
        return f.read().strip()


def get_dom(url: str):
    dom = urlparse(url).netloc.lower()
    prefix, tail = dom.split(".", 1)
    if prefix.startswith("www") and len(prefix) < 5:
        return tail
    return dom


def wirte_clave(db: DBLite, f: TextIOWrapper, label: str, table: str):
    f.write("\n"+dedent(f'''
        # {label}

        | id | txt |
        |---:|-----|
    ''').strip()+"\n")
    for id, txt in db.select(f"select id, txt from {table} order by id, txt"):
        if txt == "¿?":
            f.write(f"| {id} | [{txt}](https://github.com/s-nt-s/age-db/issues/1) |\n")
        else:
            f.write(f"| {id} | {txt} |\n")


readme = FM.resolve_path("README.md")
SPLIT = "# "
content = "\n" + SPLIT + read(readme).split(SPLIT, 1)[1].strip()
with DBLite(ARG.db, readonly=True) as db:
    with open(readme, "w") as f:
        f.write("Crea una base de datos `sqlite` a partir del:\n\n")
        for url, txt, via in db.select("select fuente, id, via from FUENTE order by id"):
            if via in (url, None):
                f.write(f"* [{txt}]({url})\n")
            else:
                f.write(f"* [{txt}]({url}) (via [{get_dom(via)}]({via}))\n")
        f.write(content)

    with open(FM.resolve_path("CLAVES.md"), "w") as f:
        f.write("Listado de claves:\n")
        for t, l in sorted(({
            "ADMINISTRACION": "Administración",
            "FORMACION": "Formación",
            "OBSERVACION": "Observación",
            "PROVISION": "Provisión",
            "TIPO_PUESTO": "Tipo puesto",
            "TITULACION": "Titulación",
            "CUERPO": "Cuerpo"
        }).items(), key=lambda x: (db.one(f"select count(*) from {x[0]}"), x)):
            wirte_clave(db, f, l, t)
