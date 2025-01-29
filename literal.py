from core.filemanager import FM
from core.web import Web, get_text

FILE = "rec/literal.txt"
literal = set(FM.load_tuple("rec/literal.txt"))
w = Web()


w.get("https://es.wikipedia.org/wiki/Anexo:Capitales_de_Estado")
for a in w.soup.select("a"):
    txt = get_text(a)
    if txt is None or txt.isdigit() or not a.attrs["href"].startswith("https://es.wikipedia.org/wiki/"):
        a.extract()
for td in w.soup.select("tbody td"):
    a = td.find("a")
    if not a:
        continue
    txt = get_text(a)
    for word in txt.split("/"):
        literal.add(word.strip())

w.get("https://www.ine.es/daco/daco42/codmun/cod_ccaa_provincia.htm")
for td in w.soup.select(".tablaCat tbody td"):
    txt = get_text(td)
    if txt and not txt.isdigit():
        for word in txt.split("/"):
            literal.add(word.strip())


def sort_key(s: str):
    return (-len(s), s.lower())


arr = sorted(literal, key=sort_key)
FM.dump(FILE, "\n".join(arr))


replace = sorted(FM.load_dict("rec/replace.txt").items(), key=lambda kv: (sort_key(kv[0]), sort_key(kv[1])))
fmt_line = "{:<%s}    {}" % max(len(kv[0]) for kv in replace)
FM.dump("rec/replace.txt", "\n".join(map(lambda kv: fmt_line.format(kv[0].lower(), kv[1]), replace)))
