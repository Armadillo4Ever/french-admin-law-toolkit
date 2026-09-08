#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tableaux du Conseil constitutionnel (données ouvertes, licence Etalab).
- maj_qpc_instance() : récupère le tableau des QPC EN INSTANCE (pendantes) et l'enregistre.
- qpc_pendante_sur(code, article) : indique si une QPC est pendante sur une disposition.
Source (rendue côté serveur, pas de navigateur nécessaire) :
  https://www.conseil-constitutionnel.fr/decisions/affaires-en-instances
À rafraîchir régulièrement (le tableau évolue en permanence).
"""
import os, re, json, time, urllib.request
from html.parser import HTMLParser

WORK = os.environ.get("CONSTIT_DOSSIER") or os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(WORK, "constit_qpc_instance.json")
URL = "https://www.conseil-constitutionnel.fr/decisions/affaires-en-instances"

class _Table(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=None; self.cell=None; self.buf=[]; self.intd=False
    def handle_starttag(self,t,a):
        if t=="tr": self.row=[]
        elif t=="td" and self.row is not None: self.intd=True; self.buf=[]
    def handle_endtag(self,t):
        if t=="td" and self.intd:
            self.row.append(" ".join(" ".join(self.buf).split())); self.intd=False
        elif t=="tr" and self.row is not None:
            if self.row: self.rows.append(self.row)
            self.row=None
    def handle_data(self,d):
        if self.intd: self.buf.append(d)

def _fetch(url):
    req=urllib.request.Request(url, headers={"User-Agent": os.environ.get("CONSTIT_UA", "Mozilla/5.0")} )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8","replace")

AFF = re.compile(r"^\s*(\d{4}-[\d/]+)\s+(QPC|DC|LOM|LP|L|AN|RIP|FNR)\b")

def maj_qpc_instance():
    html=_fetch(URL)
    p=_Table(); p.feed(html)
    qpc=[]
    for row in p.rows:
        m=AFF.match(row[0] if row else "")
        if not m: continue
        affaire=f"{m.group(1)} {m.group(2)}"
        disposition=row[1] if len(row)>1 else ""
        saisine=row[2] if len(row)>2 else ""
        # code(s) = avant la 1re occurrence d'"article" ; articles = tokens normalisés
        codes=re.split(r"\s{2,}|\||—", disposition)
        code=codes[0].strip() if codes else ""
        arts=re.findall(r"(?:articles?|Lp\.?)\s*([LRDlrd]?\.?\s?[\d][\d\-\.]*)", disposition)
        arts=[re.sub(r"[\s.]","",a) for a in arts]
        qpc.append({"affaire":affaire,"nature":m.group(2),"code":code,
                    "disposition":disposition,"articles_normes":arts,"saisine":saisine})
    data={"maj":time.strftime("%Y-%m-%d %H:%M"),"source":URL,"qpc":qpc}
    json.dump(data, open(STORE,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    return data

def _load(max_age_h=24):
    if not os.path.exists(STORE) or (time.time()-os.path.getmtime(STORE))>max_age_h*3600:
        try: return maj_qpc_instance()
        except Exception:
            pass
    try: return json.load(open(STORE,encoding="utf-8"))
    except Exception: return {"qpc":[]}

def qpc_pendante_sur(code, article):
    data=_load()
    an=re.sub(r"[\s.]","",article)
    codn=re.sub(r"[^a-zàâçéèê]","",code.lower())
    hits=[]
    for q in data.get("qpc",[]):
        dispn=re.sub(r"[\s.]","",q["disposition"])
        code_ok = codn[:12] in re.sub(r"[^a-zàâçéèê]","",q["disposition"].lower())
        if an and an in dispn and code_ok:
            hits.append({"affaire":q["affaire"],"disposition":q["disposition"],
                         "lien":"https://www.conseil-constitutionnel.fr/decisions/affaires-en-instances"})
    return hits

if __name__=="__main__":
    d=maj_qpc_instance()
    print(f"MAJ {d['maj']} — {len(d['qpc'])} QPC en instance")
    for q in d["qpc"][:12]:
        print(f"  {q['affaire']} | {q['code']} | arts={q['articles_normes']}")
