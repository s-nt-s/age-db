import json
import logging
from os import makedirs
from os.path import dirname, realpath
from pathlib import Path
import pdftotext
from typing import List, Dict
from types import MappingProxyType
import re

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class FileManager:
    """
    Da funcionalidad de lectura (load) y escritura (dump) de ficheros
    """

    def __init__(self, root=None):
        """
        Parameters
        ----------
        root: str | Path
            por defecto es la raiz del proyecto, es decir, el directorio ../.. al de este fichero
            se usa para interpretar que las rutas relativas son relativas a este directorio root
        """
        if root is None:
            root = Path(dirname(realpath(__file__))).parent
        elif isinstance(root, str):
            root = Path(root)

        self.root = root

    def resolve_path(self, file) -> Path:
        """
        Si es una ruta absoluta se devuelve tal cual
        Si es una ruta relativa se devuelve bajo la ruta root
        Si empieza por ~ se expande

        Parameters
        ----------
        file: str | Path
            Ruta a resolver
        """
        if isinstance(file, str):
            file = Path(file)

        if str(file).startswith("~"):
            file = file.expanduser()

        if file.is_absolute():
            return file

        root_file = self.root.joinpath(file)

        return root_file

    def exists(self, file) -> True:
        f = self.resolve_path(file)
        return f.exists()

    def normalize_ext(self, ext: str) -> str:
        """
        Normaliza extensiones para identificar el tipo de fichero en base a la extension
        """
        ext = ext.lstrip(".")
        ext = ext.lower()
        return {
            "xlsx": "xls",
            "js": "json",
            "sql": "txt",
            "csv": "txt",
            "htm": "html"
        }.get(ext, ext)

    def load(self, file, *args, not_exist_ok=False, **kwargs):
        """
        Lee un fichero en funcion de su extension
        Para que haya soporte para esa extension ha de exisitir una funcion load_extension
        """
        file = self.resolve_path(file)
        if not_exist_ok and not file.exists():
            return None

        ext = self.normalize_ext(file.suffix)

        load_fl = getattr(self, "load_"+ext, None)
        if load_fl is None:
            raise Exception(f"No existe metodo para leer ficheros {ext} [{file.name}]")

        return load_fl(file, *args, **kwargs)

    def dump(self, file, obj, *args, **kwargs):
        """
        Guarda un fichero en funcion de su extension
        Para que haya soporte para esa extension ha de exisitir una funcion dump_extension
        """
        file = self.resolve_path(file)
        self.makedirs(file)

        if isinstance(obj, bytes):
            with open(file, "wb") as f:
                f.write(obj)
            return

        if isinstance(obj, str):
            with open(file, "w") as f:
                f.write(obj)
            return

        ext = self.normalize_ext(file.suffix)

        dump_fl = getattr(self, "dump_"+ext, None)
        if dump_fl is None:
            raise Exception(f"No existe metodo para guardar ficheros {ext} [{file.name}]")

        dump_fl(file, obj, *args, **kwargs)

    def makedirs(self, file):
        file = self.resolve_path(file)
        makedirs(file.parent, exist_ok=True)

    def load_json(self, file, *args, **kwargs):
        with open(file, "r") as f:
            return json.load(f, *args, **kwargs)

    def dump_json(self, file, obj, *args, indent=2, **kwargs):
        with open(file, "w") as f:
            json.dump(obj, f, *args, indent=indent, **kwargs)

    def load_html(self, file, *args, parser="lxml", **kwargs):
        with open(file, "r") as f:
            return BeautifulSoup(f.read(), parser)

    def dump_html(self, file, obj, *args, **kwargs):
        if isinstance(obj, (BeautifulSoup, Tag)):
            obj = str(obj)
        with open(file, "w") as f:
            f.write(obj)

    def load_txt(self, file, *args, **kwargs):
        with open(file, "r") as f:
            txt = f.read()
            if args or kwargs:
                txt = txt.format(*args, **kwargs)
            return txt

    def dump_txt(self, file, txt, *args, **kwargs):
        if args or kwargs:
            txt = txt.format(*args, **kwargs)
        with open(file, "w") as f:
            f.write(txt)

    def load_pdf(self, file, *args, as_list=False, **kvargs):
        with open(file, 'rb') as fl:
            pdf = pdftotext.PDF(fl, **kvargs)
            if as_list:
                return list(pdf)
            return "\n".join(pdf)

    def load_tuple(self, file, *args, **kwargs):
        txt = self.load_txt(file, *args, **kwargs)
        arr: List[str] = []
        for ln in txt.strip().split("\n"):
            ln = ln.strip()
            if len(ln) > 0:
                arr.append(ln)
        return tuple(arr)

    def load_dict(self, file, *args, **kwargs):
        lines = self.load_tuple(file, *args, **kwargs)
        dct: Dict[str, str] = {}
        for ln in lines:
            k, v = re.split(r"  +|\t|[ \t]{2,}", ln)
            dct[k] = v
        return MappingProxyType(dct)


# Mejoras dinámicas en la documentación
for mth in dir(FileManager):
    slp = mth.split("_", 1)
    if len(slp) == 2 and slp[0] in ("load", "dump"):
        key, ext = slp
        mth = getattr(FileManager, mth)
        if mth.__doc__ is None:
            if key == "load":
                mth.__doc__ = "Lee "
            else:
                mth.__doc__ = "Guarda "
            mth.__doc__ = mth.__doc__ + "un fichero de tipo "+ext

FM = FileManager()
