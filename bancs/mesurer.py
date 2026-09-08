#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mesure d'un moteur de recherche juridique sur un banc de questions.

    python3 mesurer.py --banc fichage/banc_fichage.jsonl --adaptateur mon_moteur.py
    python3 mesurer.py --banc b.jsonl --adaptateur m.py --k 20 --sortie avant.json
    python3 mesurer.py --comparer avant.json apres.json

L'adaptateur est un module Python qui expose :

    chercher(question, k, fonds) -> {"nom du fonds": [document, ...], ...}

où chaque document est un dictionnaire quelconque : le banc y cherche lui-même les
identifiants (numéro de décision, LEGIARTI, CELEX, numéro de pourvoi, requête CEDH,
article d'un code, numéro de loi ou de décret), quel que soit le nom des champs. Une
liste plate est acceptée : elle est traitée comme un fonds unique.

CE QUE LES CHIFFRES VALENT. Les jugements de pertinence d'un banc sont incomplets par
construction : ils ne contiennent que ce qui a été jugé. Une source excellente absente
du banc compte comme non pertinente et pénalise injustement le moteur. Les chiffres
servent à COMPARER deux configurations sur le même banc, jamais à mesurer une qualité
absolue.

Bibliothèque standard uniquement.
"""

import argparse
import json
import math
import os
import re
import sys
import time


# --------------------------------------------------------------------------- identifiants
CHAMPS_CLE = ("numero", "cle", "id", "identifiant", "celex", "ecli", "requete",
              "appno", "legiarti", "numero_pourvoi", "num")
CHAMPS_TEXTE = ("reference", "titre", "ref", "lien", "url", "intitule")

_NUM = re.compile(r"\bn[°o]\s*(\d{4,7})\b")
_MOTIFS = [
    re.compile(r"\b(\d{4,7})\b"),                                              # décision CE
    re.compile(r"\b(\d{2}-\d{5})\b"),                                          # pourvoi Cass.
    re.compile(r"\b(\d{4}-\d{1,4}\s?(?:QPC|DC|LP|L|FNR))\b", re.I),            # Cons. const.
    re.compile(r"\b(\d{3,6}/\d{2})\b"),                                        # requête CEDH
    re.compile(r"\b([CT]-\d{1,3}/\d{2})\b"),                                   # affaire CJUE
    re.compile(r"\b((?:LEGIARTI|JORFTEXT|JURITEXT|LEGITEXT|JORFARTI|CONSTEXT)\d{12})\b"),
    re.compile(r"\b(3\d{4}[LRD]\d{4}|6\d{4}[CT][JC]\d{4})\b"),                 # CELEX
    re.compile(r"i=(\d{3}-\d{4,7})\b"),                                        # HUDOC
]
_JOINTS = re.compile(r"n[°o]s?\s*((?:\d{4,7}(?![/\d])\s*(?:,|et)\s*)+\d{4,7}(?![/\d]))")
_ART = re.compile(r"\b(?:art\.?|article)\s+((?:[LRD]\.?\s*)?\d{1,4}(?:-\d{1,3}){0,3}(?:\s*[A-Z]\b)?)", re.I)
_TEXTE = re.compile(r"\b(loi|ordonnance|décret|decret)\s*(?:organique\s*)?n[°o]\s*(\d{2,4}-\d{1,5})", re.I)
_GENRES = {"loi": "loi", "ordonnance": "ord", "décret": "decret", "decret": "decret"}


def normaliser(cle):
    """Même identifiant, même écriture : « 08-03.639 » et « 08-03639 », « 2018-761 QPC »
    et « 2018-761QPC » doivent se rencontrer."""
    return str(cle).strip().lower().replace(" ", "").replace(".", "").replace(" ", "")


def cles_doc(rec):
    """Ensemble des identifiants d'un document, normalisés.

    Un moteur ne rend pas ses résultats sous la forme qu'attend le banc. Plutôt que
    d'imposer un champ, on ratisse : champs d'identifiant connus, liens, et motifs
    reconnus dans les textes de référence."""
    out = set()
    if not isinstance(rec, dict):
        if isinstance(rec, str):
            rec = {"reference": rec}
        else:
            return out
    for c in CHAMPS_CLE:
        v = rec.get(c)
        if isinstance(v, (int, float)):
            v = str(v)
        if isinstance(v, str) and v.strip():
            out.add(normaliser(v))
    liens = rec.get("liens")
    if isinstance(liens, dict):
        for v in liens.values():
            if isinstance(v, str):
                out.add(normaliser(v))
    textes = [rec.get(c) for c in CHAMPS_TEXTE if isinstance(rec.get(c), str)]
    textes += list(out)
    for t in textes:
        for m in _MOTIFS:
            for g in m.findall(t):
                out.add(normaliser(g))
        for grp in _JOINTS.findall(t):              # « n° 276069, 277198, 277460 »
            for g in re.findall(r"\d{4,7}", grp):
                out.add(g)
        for g in _ART.findall(t):
            out.add("art:" + normaliser(g))
        for genre, num in _TEXTE.findall(t):
            out.add("%s:%s" % (_GENRES[genre.lower()], num))
    ref = rec.get("reference")
    if isinstance(ref, str):
        m = _NUM.search(ref)
        if m:
            out.add(m.group(1))
    return {c for c in out if c}


def cle_affichage(rec):
    """Identifiant lisible d'un document, pour les journaux."""
    if isinstance(rec, str):
        return rec[:60]
    if not isinstance(rec, dict):
        return None
    ref = rec.get("reference")
    if isinstance(ref, str):
        m = _NUM.search(ref)
        if m:
            return m.group(1)
    for c in CHAMPS_CLE:
        v = rec.get(c)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, (int, float)):
            return str(v)
    liens = rec.get("liens")
    if isinstance(liens, dict):
        for v in liens.values():
            if isinstance(v, str):
                return v
    return None


def famille(cle):
    """Famille d'une source attendue, d'après la forme de son identifiant."""
    c = normaliser(cle)
    if re.match(r"^\d{4,7}$", c): return "CE"
    if re.match(r"^\d{3,6}/\d{2}$", c): return "CEDH"
    if re.match(r"^[ct]-\d", c) or re.match(r"^6\d{4}[ct][jc]", c): return "CJUE"
    if re.search(r"(qpc|dc|lp|l)$", c) and re.match(r"^\d{2,4}-\d", c): return "Cons. const."
    if re.match(r"^\d{2}-\d{5}$", c): return "Cass."
    if re.match(r"^3\d{4}[lrd]\d{4}$", c): return "texte UE"
    if c.startswith(("legiarti", "jorftext", "jorfarti", "legitext",
                     "art:", "loi:", "ord:", "decret:")): return "Légifrance"
    return "autre"


# --------------------------------------------------------------------------- mesures
def aplatir(resultats):
    """{fonds: [doc]} -> liste ordonnée de (affichage, identifiants), fonds après fonds.

    L'ordre entre fonds est une convention d'affichage ; ce qui est mesuré est la
    capacité à faire remonter les bonnes sources, non l'ordonnancement inter-fonds."""
    if isinstance(resultats, list):
        resultats = {"resultats": resultats}
    plat, vus = [], set()
    for _fonds, lst in (resultats or {}).items():
        for rec in (lst or []):
            aff = cle_affichage(rec)
            if not aff or aff in vus:
                continue
            vus.add(aff)
            plat.append((aff, cles_doc(rec)))
    return plat


def _gain(item, pertinences):
    """Note attendue d'un résultat : la meilleure des notes de ses identifiants."""
    return max([pertinences.get(c, 0) for c in item[1]] or [0])


def ndcg(classement, pertinences, p=10):
    """Gain cumulé actualisé : récompense une source pertinente d'autant plus qu'elle
    est haut placée. 1,0 = ordre parfait."""
    dcg = 0.0
    for i, c in enumerate(classement[:p]):
        g = _gain(c, pertinences)
        if g:
            dcg += (2 ** g - 1) / math.log2(i + 2)
    ideal = sorted(pertinences.values(), reverse=True)[:p]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return (dcg / idcg) if idcg else 0.0


def rappel(classement, pertinences, p=50):
    """Part des sources attendues effectivement retrouvées dans les p premiers."""
    if not pertinences:
        return 0.0
    touchees = set()
    for c in classement[:p]:
        touchees |= {k for k in c[1] if k in pertinences}
    return len(touchees) / len(pertinences)


def rang_premier(classement, pertinences):
    """Rang de la première source attendue. Le chiffre que ressent celui qui cherche."""
    for i, c in enumerate(classement):
        if _gain(c, pertinences):
            return i + 1
    return None


def touchees_par_fonds(resultats, pertinences):
    """Pour chaque fonds, les attendus qu'il a rendus et leur rang DANS ce fonds.
    C'est la lecture juste d'une recherche multi-fonds : le rang à l'intérieur d'un
    fonds est ce que voit l'œil."""
    if isinstance(resultats, list):
        resultats = {"resultats": resultats}
    out = {}
    for fonds, lst in (resultats or {}).items():
        vus = []
        for rang, rec in enumerate(lst or [], 1):
            for k in cles_doc(rec) & set(pertinences):
                if k not in [v[1] for v in vus]:
                    vus.append((rang, k))
        if lst:
            out[fonds] = {"n": len(lst), "touchees": vus}
    return out


# --------------------------------------------------------------------------- exécution
def charger_banc(chemin):
    lignes = []
    with open(chemin, encoding="utf-8") as f:
        for n, l in enumerate(f, 1):
            l = l.strip()
            if not l or l.startswith("//"):
                continue
            try:
                lignes.append(json.loads(l))
            except json.JSONDecodeError as e:
                print("  ligne %d illisible, ignorée : %s" % (n, e))
    return lignes


def charger_adaptateur(chemin):
    if chemin.endswith(".py"):
        nom = os.path.splitext(os.path.basename(chemin))[0]
        sys.path.insert(0, os.path.dirname(os.path.abspath(chemin)) or ".")
        return __import__(nom)
    return __import__(chemin)


def mesurer(banc, adaptateur, k, p_rappel, verbeux=False):
    chercher = getattr(adaptateur, "chercher", None)
    if chercher is None:
        print("L'adaptateur n'expose pas de fonction chercher(question, k, fonds).")
        return None

    lignes, t0 = [], time.time()
    for q in banc:
        pertinences = {normaliser(a["cle"]): int(a.get("note", 1))
                       for a in q.get("attendus", [])}
        debut = time.time()
        try:
            resultats = chercher(q["question"], k, q.get("fonds"))
            erreur = None
        except Exception as e:
            resultats, erreur = {}, repr(e)[:140]
        duree = time.time() - debut

        plat = aplatir(resultats)
        ligne = {
            "id": q.get("id"),
            "question": q["question"][:120],
            "attendus": len(pertinences),
            "ndcg10": round(ndcg(plat, pertinences, 10), 4),
            "rappel": round(rappel(plat, pertinences, p_rappel), 4),
            "rang_premier": rang_premier(plat, pertinences),
            "rendus": len(plat),
            "secondes": round(duree, 2),
            "par_fonds": touchees_par_fonds(resultats, pertinences),
            "familles": sorted({famille(c) for c in pertinences}),
        }
        if erreur:
            ligne["erreur"] = erreur
        lignes.append(ligne)
        if verbeux:
            print("  %-6s ndcg %.2f  rappel %.2f  rang %s  %5.2fs  %s"
                  % (ligne["id"], ligne["ndcg10"], ligne["rappel"],
                     ligne["rang_premier"] or "-", ligne["secondes"], ligne["question"][:60]))

    n = len(lignes) or 1
    trouves = [l for l in lignes if l["rang_premier"]]
    resume = {
        "questions": len(lignes),
        "ndcg10": round(sum(l["ndcg10"] for l in lignes) / n, 4),
        "rappel": round(sum(l["rappel"] for l in lignes) / n, 4),
        "p_rappel": p_rappel,
        "k": k,
        "trouvees": len(trouves),
        "part_trouvees": round(len(trouves) / n, 4),
        "rang_median": (sorted(l["rang_premier"] for l in trouves)[len(trouves) // 2]
                        if trouves else None),
        "mrr": round(sum(1.0 / l["rang_premier"] for l in trouves) / n, 4),
        "secondes_totales": round(time.time() - t0, 1),
        "erreurs": sum(1 for l in lignes if l.get("erreur")),
    }
    return {"resume": resume, "lignes": lignes}


def afficher(rapport):
    r = rapport["resume"]
    print("\n  questions            : %d" % r["questions"])
    print("  au moins une trouvée : %d  (%.0f %%)" % (r["trouvees"], 100 * r["part_trouvees"]))
    print("  nDCG@10 moyen        : %.3f" % r["ndcg10"])
    print("  rappel@%-3d moyen     : %.3f" % (r["p_rappel"], r["rappel"]))
    print("  MRR                  : %.3f" % r["mrr"])
    print("  rang médian du 1er   : %s" % (r["rang_median"] or "aucun"))
    print("  durée                : %.1f s" % r["secondes_totales"])
    if r["erreurs"]:
        print("  questions en erreur  : %d" % r["erreurs"])


def comparer(avant, apres):
    a = json.load(open(avant, encoding="utf-8"))["resume"]
    b = json.load(open(apres, encoding="utf-8"))["resume"]
    print("\n  %-22s %10s %10s %10s" % ("", "avant", "après", "écart"))
    for cle, libelle, fmt in (("part_trouvees", "au moins une trouvée", "%.3f"),
                              ("ndcg10", "nDCG@10", "%.3f"),
                              ("rappel", "rappel", "%.3f"),
                              ("mrr", "MRR", "%.3f")):
        va, vb = a.get(cle), b.get(cle)
        if va is None or vb is None:
            continue
        print("  %-22s %10s %10s %10s"
              % (libelle, fmt % va, fmt % vb, ("%+.3f" % (vb - va))))
    if a.get("rang_median") and b.get("rang_median"):
        print("  %-22s %10d %10d %10d" % ("rang médian du 1er", a["rang_median"],
                                          b["rang_median"], b["rang_median"] - a["rang_median"]))
    print("\n  Un écart n'a de sens qu'entre deux mesures du MÊME banc, avec le même k.")


def main():
    ap = argparse.ArgumentParser(description="Mesure d'un moteur de recherche sur un banc")
    ap.add_argument("--banc", help="JSONL des questions")
    ap.add_argument("--adaptateur", help="chemin d'un .py ou nom de module exposant chercher()")
    ap.add_argument("--k", type=int, default=10, help="résultats demandés par fonds (défaut 10)")
    ap.add_argument("--rappel", type=int, default=50, help="profondeur du rappel (défaut 50)")
    ap.add_argument("--sortie", help="écrire le rapport détaillé dans ce fichier JSON")
    ap.add_argument("-v", "--verbeux", action="store_true")
    ap.add_argument("--comparer", nargs=2, metavar=("AVANT", "APRES"),
                    help="comparer deux rapports déjà produits")
    args = ap.parse_args()

    if args.comparer:
        comparer(*args.comparer)
        return 0
    if not args.banc or not args.adaptateur:
        ap.error("--banc et --adaptateur sont requis (ou --comparer)")

    banc = charger_banc(args.banc)
    adaptateur = charger_adaptateur(args.adaptateur)
    print("=== MESURE ===")
    print("    banc       : %s  (%d questions)" % (args.banc, len(banc)))
    print("    adaptateur : %s" % args.adaptateur)
    print("    k = %d, rappel@%d\n" % (args.k, args.rappel))

    rapport = mesurer(banc, adaptateur, args.k, args.rappel, args.verbeux)
    if rapport is None:
        return 1
    afficher(rapport)
    if args.sortie:
        with open(args.sortie, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=1)
        print("\n  rapport écrit dans %s" % args.sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
