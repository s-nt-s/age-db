from core.dblite import DBLite
import argparse
from textwrap import dedent
from urllib.parse import urlparse

parser = argparse.ArgumentParser(
    description='Reescribe README.md',
)
parser.add_argument(
    '--db', type=str, default="out/age.sqlite"
)
parser.add_argument(
    '--md', type=str, default="README.md"
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


SPLIT = "# "
content = "\n" + SPLIT + read(ARG.md).split(SPLIT, 1)[1].strip()
with open(ARG.md, "w") as f:
    f.write("Crea una base de datos `sqlite` a partir del:\n\n")
    with DBLite(ARG.db, readonly=True) as db:
        for url, txt, via in db.select("select fuente, id, via from FUENTE"):
            if via in (url, None):
                f.write(f"* [{txt}]({url})\n")
            else:
                f.write(f"* [{txt}]({url}) (via [{get_dom(via)}]({via}))\n")
    f.write(content)
