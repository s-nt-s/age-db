import requests
import xmltodict
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import pytz



re_num = re.compile(r"\d+")
re_sp = re.compile(r"\s+")


class BoeApi:
    def __init__(self):
        pass

    def get(self, id):
        r = requests.get("https://www.boe.es/diario_boe/xml.php?id="+id)
        js = xmltodict.parse(r.text)
        return js

    def safe_get(self, url):
        prs = urlparse(url)
        if prs.query is None:
            return None
        dom = prs.netloc
        if dom != "www.boe.es":
            return None
        qsl = parse_qs(prs.query)
        ids = qsl.get("id")
        if ids is None or len(ids) == 0:
            return None
        id = ids[0]
        return BOE(id)


class BOE:
    def __init__(self, id: str):
        if id.startswith("http"):
            pr = urlparse(id)
            qr = parse_qs(pr.query)
            id = qr['id'][0]
        self.__js = BoeApi().get(id)

    @property
    def meta(self):
        return self.__js['documento']['metadatos']

    @property
    def id(self):
        return self.meta['identificador']

    @property
    def title(self):
        if self.meta['numero_oficial'] is None:
            return self.titulo
        r = []
        r.append(self.meta['rango']['#text'])
        r.append(self.meta['numero_oficial'])
        return " ".join(r)

    @property
    def numero(self):
        return self.meta['numero_oficial']

    @property
    def titulo(self):
        r = []
        tt = re_sp.sub(" ", self.meta['titulo']).strip()
        for t in tt.split(","):
            t = t.strip()
            if len(t) == 0:
                continue
            if not re_num.search(t):
                break
            r.append(t)
        return ", ".join(r)

    @property
    def modificado(self):
        md = self.__js['documento']['@fecha_actualizacion']
        dt = datetime.strptime(md, '%Y%m%d%H%M%S')
        tz = pytz.timezone('Europe/Madrid')
        dt = tz.localize(dt)
        return dt
