# -*- coding: utf-8 -*-
"""Connecteur Judilibre (API ouverte de la Cour de cassation, via PISTE).

Recherche en langage naturel dans la jurisprudence judiciaire (Cour de cassation,
cours d'appel), avec niveau de publication (P/B/R/L) analogue a la hierarchie Lebon.
Reutilise l'authentification OAuth PISTE de legifrance.py (memes identifiants locaux,
jamais transmis). Prerequis : abonner l'API Judilibre a l'application PISTE (comme
Legifrance), sinon 403.
"""
import json, urllib.parse, urllib.request

try:
    import legifrance  # reutilise token() / _creds() / _iso()
except Exception:
    legifrance = None

BASE = "https://api.piste.gouv.fr/cassation/judilibre/v1.0"

# libelles de publication Judilibre
_PUB = {"p": "Publie", "b": "Bulletin", "r": "Rapport annuel",
        "l": "Lettre de chambre", "c": "Communique", "n": "Inedit"}
# niveau synthetique pour la hierarchie (plus haut = plus publie)
_PUB_RANG = {"r": 3, "b": 2, "p": 2, "l": 1, "c": 1, "n": 0}


def _niveau(pub):
    if not pub:
        return "inedit", 0
    codes = [p.lower() for p in pub]
    best = max(codes, key=lambda c: _PUB_RANG.get(c, 0))
    return _PUB.get(best, best), _PUB_RANG.get(best, 0)


def _lien(idd):
    return f"https://www.courdecassation.fr/decision/{idd}" if idd else ""


def _get(path, params):
    if not legifrance:
        return {}
    tok = legifrance.token()
    if not tok:
        return {}
    url = BASE + path + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}",
                                               "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def chercher(question, k=5, publication=None, chamber=None):
    """Recherche en langage naturel. Renvoie une liste de dict :
    reference, chambre, date, numero, niveau (publication), solution, extrait, lien."""
    params = {"query": question, "operator": "or", "page_size": max(1, min(k, 50)),
              "page": 0, "sort": "score", "order": "desc", "resolve_references": "true"}
    if publication:
        params["publication"] = publication
    if chamber:
        params["chamber"] = chamber
    try:
        res = _get("/search", params)
    except Exception:
        return []
    out = []
    for h in (res.get("results") or [])[:k]:
        idd = h.get("id")
        date = h.get("decision_date") or h.get("date") or ""
        num = h.get("number") or (h.get("numbers") or [None])[0] or ""
        cham = h.get("chamber") or ""
        juri = h.get("jurisdiction") or "Cour de cassation"
        niv, rang = _niveau(h.get("publication"))
        # extrait : premier highlight, sinon sommaire
        hi = h.get("highlights") or {}
        frags = []
        for v in hi.values():
            frags += v if isinstance(v, list) else [v]
        extrait = (frags[0] if frags else (h.get("summary") or "")) or ""
        jlabel = "Cass." if "cassation" in str(juri).lower() else str(juri)
        ref = f'{jlabel} {cham}, {date}, n° {num} ({niv})'.replace(" ,", ",")
        out.append({"reference": ref.strip(), "juridiction": juri, "chambre": cham,
                    "date": date, "numero": num, "niveau": niv, "rang": rang,
                    "solution": h.get("solution") or "", "extrait": extrait[:600],
                    "lien": _lien(idd), "id": idd})
    # hierarchie : plus publie d'abord, puis plus recent
    out.sort(key=lambda d: (d["rang"], d["date"]), reverse=True)
    return out


def sante():
    try:
        return _get("/healthcheck", {})
    except Exception as e:
        return {"erreur": repr(e)}


if __name__ == "__main__":
    print("healthcheck:", sante())
    for q in ["responsabilite du fait des produits defectueux",
              "trouble anormal de voisinage"]:
        print("\n==", q)
        for d in chercher(q, k=3):
            print("  ", d["reference"], "->", d["lien"])
            if d["extrait"]:
                print("      ", d["extrait"][:120].replace("\n", " "))
