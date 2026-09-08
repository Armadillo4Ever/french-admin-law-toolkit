#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fabrique un banc de recherche juridique à partir du fichage de la jurisprudence.

IDÉE. Chaque analyse associe un point de droit rédigé par un magistrat à la décision
qui l'a posé. C'est un couple question-réponse produit par un expert, et il y en a des
dizaines de milliers dans l'open data. Aucune annotation à faire.

CE QUE LE BANC MESURE. Partant de l'énoncé d'une règle, le moteur retrouve-t-il la
décision qui l'a posée ? C'est la recherche « je cherche LA bonne réponse ». Ce n'est
pas la recherche par analogie, qui appelle un autre banc.

SANS FUITE. La question étant tirée d'une analyse, interroger le corpus des analyses la
retrouverait telle quelle et la mesure serait nulle. Le banc porte donc la mention
`cible: decisions` : seul le texte intégral des décisions doit être interrogé.

    python3 construire_banc.py --analyses analyses.jsonl --decisions decisions_ids.jsonl
    python3 construire_banc.py --analyses a.jsonl --decisions d.jsonl -n 500 --graine 7

Le format des deux fichiers d'entrée est décrit dans FORMAT.md.
Bibliothèque standard uniquement.
"""

import argparse
import json
import os
import random
import re
import sys


# --------------------------------------------------------------------------- entrées
def numeros_indexes(chemins):
    """Décisions réellement disponibles en texte intégral. Une décision absente du
    corpus interrogé serait introuvable : la retenir fausserait la mesure vers le bas."""
    nums = set()
    for p in chemins:
        if not os.path.exists(p):
            print("  fichier de décisions introuvable, ignoré : %s" % p)
            continue
        with open(p, encoding="utf-8") as f:
            for ligne in f:
                try:
                    r = json.loads(ligne)
                except Exception:
                    continue
                n = r.get("numero") or r.get("id")
                if n:
                    nums.add(str(n).strip())
    return nums


# --------------------------------------------------------------------------- énoncé
def _part_majuscules(bloc):
    lettres = [c for c in bloc if c.isalpha()]
    if not lettres:
        return 1.0
    return sum(1 for c in lettres if c.isupper()) / len(lettres)


_CODE = re.compile(r"^\s*(\d{2}(?:-\d{2})*)?\s*:?\s*")


def titrage(abrege, mini=60, maxi=700):
    """Extrait l'énoncé du point de droit, et rien d'autre.

    Un abrégé se présente en trois temps : le code et le chemin du plan de classement,
    puis le titrage (la chaîne de mots-clés qui énonce le point), puis le résumé.

    Le chemin de classement doit être écarté sans pitié : il est rédigé en capitales et
    n'énonce aucune question de droit, seulement une rubrique. Le retenir reviendrait à
    mesurer une correspondance de nomenclature, pas une recherche juridique. Les fichages
    anciens se réduisent souvent à ce chemin : ils sont donc écartés, et le banc penchera
    vers les décisions plus récentes. C'est un biais assumé, préférable à des questions
    vides de sens.

    Retourne (énoncé, genre) où genre vaut "titrage" ou "resume".
    """
    if not abrege:
        return None, None
    blocs = [b.strip() for b in re.split(r"\n\s*\n", abrege) if b.strip()]
    if len(blocs) < 2:
        return None, None
    resume = None
    for bloc in blocs[1:]:
        b = " ".join(bloc.split())
        b = _CODE.sub("", b).strip()
        if len(b) < mini or len(b) > maxi:
            continue
        if _part_majuscules(b) > 0.55:          # chemin du plan de classement
            continue
        if len(b.split()) < 10:
            continue
        est_resume = bool(re.match(r"^\d\)", b)) or (b.count("-") < 2 and b.count("–") < 2)
        if not est_resume:
            return b, "titrage"
        if resume is None:
            resume = b
    # À défaut de titrage exploitable, le résumé fait un énoncé acceptable, plus proche
    # des mots de la décision : on le signale pour pouvoir mesurer les deux séparément.
    return (resume, "resume") if resume else (None, None)


def decennie(date):
    m = re.match(r"(\d{4})", str(date or ""))
    return (int(m.group(1)) // 10) * 10 if m else 0


# --------------------------------------------------------------------------- construction
def construire(analyses, decisions, cible, graine, sortie, office="contentieux"):
    indexes = numeros_indexes(decisions)
    print("Décisions disponibles en texte intégral : %d" % len(indexes))

    retenus, vus = [], set()
    ecartes = {"sans_titrage": 0, "hors_index": 0, "doublon": 0}
    for chemin in analyses:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                try:
                    r = json.loads(ligne)
                except Exception:
                    continue
                num = r.get("numero")
                num = str(num).strip() if num else None
                if not num or (indexes and num not in indexes):
                    ecartes["hors_index"] += 1
                    continue
                if num in vus:
                    ecartes["doublon"] += 1     # une décision peut porter plusieurs analyses
                    continue
                q, genre = titrage(r.get("abrege"))
                if not q:
                    ecartes["sans_titrage"] += 1
                    continue
                vus.add(num)
                retenus.append({"numero": num, "question": q, "genre": genre,
                                "classement": r.get("classement") or "?",
                                "decennie": decennie(r.get("date")), "date": r.get("date")})

    print("Analyses exploitables : %d" % len(retenus))
    print("  écartées : %s" % ecartes)
    if not retenus:
        return 1

    # Tirage stratifié par niveau de classement et par décennie : sans quoi le banc
    # serait massivement composé de décisions récentes du niveau le plus fourni.
    strates = {}
    for r in retenus:
        strates.setdefault((r["classement"], r["decennie"]), []).append(r)
    rnd = random.Random(graine)
    for v in strates.values():
        rnd.shuffle(v)

    choisis, i = [], 0
    ordre = sorted(strates)
    while len(choisis) < cible and any(strates[c] for c in ordre):
        c = ordre[i % len(ordre)]
        if strates[c]:
            choisis.append(strates[c].pop())
        i += 1

    with open(sortie, "w", encoding="utf-8") as f:
        for n, r in enumerate(choisis, 1):
            f.write(json.dumps({
                "id": "f%03d" % n,
                "office": office,
                "cible": "decisions",
                "question": r["question"],
                "attendus": [{"cle": r["numero"], "note": 2}],
                "_niveau": r["classement"], "_date": r["date"], "_genre": r["genre"],
            }, ensure_ascii=False) + "\n")

    par = lambda cle: {k: sum(1 for r in choisis if r[cle] == k)
                       for k in sorted({r[cle] for r in choisis})}
    print("\nBanc écrit : %s" % sortie)
    print("  %d questions" % len(choisis))
    print("  par niveau   : %s" % par("classement"))
    print("  par décennie : %s" % par("decennie"))
    print("  par nature   : %s   (titrage = énoncé du point ; resume = résumé du fichiste)"
          % par("genre"))
    print("\nÉtape suivante :")
    print("  python3 ../mesurer.py --banc %s --adaptateur mon_moteur.py" % os.path.basename(sortie))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Construction d'un banc de recherche à partir du fichage")
    ap.add_argument("--analyses", action="append", required=True,
                    help="JSONL des analyses (répétable)")
    ap.add_argument("--decisions", action="append", default=[],
                    help="JSONL des décisions disponibles en texte intégral (répétable) ; "
                         "sans ce filtre, toutes les analyses sont candidates")
    ap.add_argument("-n", "--nombre", type=int, default=300, help="questions à tirer (défaut 300)")
    ap.add_argument("--graine", type=int, default=20260905,
                    help="graine du tirage : même graine, même banc")
    ap.add_argument("--sortie", default="banc_fichage.jsonl")
    ap.add_argument("--office", default="contentieux")
    args = ap.parse_args()
    return construire(args.analyses, args.decisions, args.nombre, args.graine,
                      args.sortie, args.office)


if __name__ == "__main__":
    sys.exit(main())
