#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Banc de légistique : exécute les 89 cas contre une implémentation quelconque.

    python3 executer.py --adaptateur mon_adaptateur.py
    python3 executer.py --adaptateur mon_adaptateur.py -v --famille lecture
    python3 executer.py --adaptateur mon_adaptateur.py --json resultats.json

L'adaptateur est un module Python qui expose, au choix, les fonctions décrites
dans FORMAT.md. Une famille dont la fonction est absente est déclarée « non
couverte » : elle ne compte ni en réussite ni en échec.

Bibliothèque standard uniquement.
"""

import argparse
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

FAMILLES = ("lecture", "traduction", "designation", "decompte",
            "articles_crees", "consolidation")

FICHIERS = {f: os.path.join(ICI, "cas_%s.jsonl" % f) for f in FAMILLES}

# Fonction attendue de l'adaptateur, pour chaque famille.
FONCTIONS = {
    "lecture": "lire",
    "traduction": "traduire",
    "designation": "resoudre",
    "decompte": "decompter",
    "articles_crees": "articles_crees",
    "consolidation": "consolider",
}


# --------------------------------------------------------------------------- chargement
def charger(famille):
    cas = []
    with open(FICHIERS[famille], encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne:
                cas.append(json.loads(ligne))
    return cas


def charger_adaptateur(chemin):
    """Accepte un chemin de fichier .py ou un nom de module importable."""
    if chemin.endswith(".py"):
        nom = os.path.splitext(os.path.basename(chemin))[0]
        dossier = os.path.dirname(os.path.abspath(chemin)) or "."
        sys.path.insert(0, dossier)
        return __import__(nom)
    return __import__(chemin)


# --------------------------------------------------------------------------- comparaison
# Les champs à valeurs fermées se comparent à l'identique. La tolérance de
# sous-chaîne, utile pour les fragments recopiés (un blanc ou un guillemet
# peuvent différer), est un piège sur un nom d'opération : « inserer_apres »
# est contenu dans « inserer_apres_mots » et passerait donc pour lui.
FERMES = ("op", "porte_sur", "cite_type", "type")


def _norme(s):
    return "".join(s.lower().split()).replace("’", "'").replace("«", '"').replace("»", '"')


def comparer(obtenu, attendu):
    """Ne compare QUE les champs annoncés par le cas : le banc ne fige pas ce qu'il n'exige pas."""
    if obtenu is None:
        return ["aucune réponse"]
    if not isinstance(obtenu, dict):
        return ["réponse de type %s, dictionnaire attendu" % type(obtenu).__name__]
    ecarts = []
    for cle, valeur in attendu.items():
        eu = obtenu.get(cle)
        if cle in FERMES:
            if eu != valeur:
                ecarts.append("%s : %r au lieu de %r" % (cle, eu, valeur))
        elif isinstance(valeur, str) and isinstance(eu, str):
            if _norme(valeur) not in _norme(eu) and _norme(eu) not in _norme(valeur):
                ecarts.append("%s : %r au lieu de %r" % (cle, eu, valeur))
        elif eu != valeur:
            ecarts.append("%s : %r au lieu de %r" % (cle, eu, valeur))
    return ecarts


# --------------------------------------------------------------------------- familles
def _appel(fonction, *args):
    try:
        return fonction(*args), None
    except Exception as e:      # une exception vaut échec, non interruption du banc
        return None, repr(e)[:120]


def eval_lecture(f, cas):
    obtenu, err = _appel(f, cas["instruction"])
    ecarts = comparer(obtenu, cas["attendu"])
    return ecarts, err, cas["instruction"][:110]


def eval_traduction(f, cas):
    obtenu, err = _appel(f, cas["instruction"])
    if isinstance(obtenu, str) or obtenu is None:
        obtenu = {"type": obtenu}
    ecarts = comparer(obtenu, {"type": cas["operation_attendue"]})
    return ecarts, err, cas["instruction"][:110]


def eval_designation(f, cas):
    obtenu, err = _appel(f, cas["article"], cas["designation"])
    ecarts = comparer(obtenu, cas["attendu"])
    return ecarts, err, cas["designation"]


def eval_decompte(f, cas):
    obtenu, err = _appel(f, cas["lignes"], cas["rang_demande"], cas["regle"])
    attendu = cas["lignes_attendues"]
    if obtenu is None:
        ecarts = ["aucune réponse"]
    elif list(obtenu) != list(attendu):
        ecarts = ["lignes %r au lieu de %r" % (obtenu, attendu)]
    else:
        ecarts = []
    return ecarts, err, "rang %s (%s)" % (cas["rang_demande"], cas["regle"])


def eval_articles_crees(f, cas):
    obtenu, err = _appel(f, cas["instruction"])
    attendu = set(cas["articles_crees"])
    if obtenu is None:
        ecarts = ["aucune réponse"]
    elif set(obtenu) != attendu:
        ecarts = ["articles %r au lieu de %r" % (sorted(obtenu), sorted(attendu))]
    else:
        ecarts = []
    return ecarts, err, cas["instruction"][:110]


def eval_consolidation(f, cas):
    res, err = _appel(f, cas["article"], cas["operations"])
    if res is None:
        return ["aucune réponse"], err, cas["operations"][0].get("designation", "")

    lignes = res.get("lignes") or []
    non_appliquees = res.get("non_appliquees") or []
    # Aplatissement : (étiquette, texte) segment par segment, et texte par ligne.
    segs = [(s.get("e") or "", s.get("t") or "") for ligne in lignes for s in ligne]
    textes_lignes = ["".join(s.get("t") or "" for s in ligne) for ligne in lignes]

    a = cas["attendu"]
    ecarts = []
    if a.get("refusee") and not non_appliquees:
        ecarts.append("l'opération aurait dû être refusée, elle a été appliquée")
    if a.get("aucun_barre") and any(e == "sup" for (e, _t) in segs):
        ecarts.append("un alinéa a été barré alors qu'aucun ne devait l'être")
    if a.get("barre") and a.get("ligne_touchee") is None:
        barres = [t for (e, t) in segs if e == "sup"]
        if not any(a["barre"][:40] in b for b in barres):
            ecarts.append("l'alinéa attendu n'est pas barré (barrés : %r)" % (barres[:2],))
    if a.get("texte") and a.get("ligne_touchee") is None and a.get("apres_alinea") is None:
        ajoutes = [t for (e, t) in segs if e == "ajo"]
        if not any(a["texte"][:40] in x for x in ajoutes):
            ecarts.append("le texte nouveau est absent (ajoutés : %r)" % (ajoutes[:2],))
    if a.get("position") is not None:
        pos = [i for i, (e, t) in enumerate(segs)
               if e == "ajo" and a["texte"][:40] in t]
        if not pos:
            ecarts.append("texte nouveau introuvable, position invérifiable")
        elif pos[0] != a["position"]:
            ecarts.append("placé en position %d au lieu de %d" % (pos[0], a["position"]))
    if a.get("apres_alinea") is not None:
        # la phrase doit être DANS la ligne de l'alinéa désigné, non dans une ligne à part
        i = a["apres_alinea"]
        if not (0 <= i < len(lignes)):
            ecarts.append("l'alinéa %d n'existe pas dans le consolidé" % i)
        elif a["texte"][:30] not in textes_lignes[i]:
            ecarts.append("la phrase n'est pas dans l'alinéa %d ; lignes : %r"
                          % (i, [t[:35] for t in textes_lignes]))
    if a.get("ligne_touchee") is not None:
        i = a["ligne_touchee"]
        if not (0 <= i < len(lignes)):
            ecarts.append("l'alinéa %d n'existe pas dans le consolidé" % i)
        else:
            marques = [(s.get("e") or "", s.get("t") or "") for s in lignes[i]]
            if a.get("barre") and not any(e == "sup" and a["barre"] in t for (e, t) in marques):
                ecarts.append("l'alinéa %d ne barre pas %r ; il porte %r" % (i, a["barre"], marques))
            if a.get("texte") and not any(e == "ajo" and a["texte"] in t for (e, t) in marques):
                ecarts.append("l'alinéa %d n'ajoute pas %r" % (i, a["texte"]))
    if a.get("contient") and not any(a["contient"] in t for t in textes_lignes):
        ecarts.append("le consolidé ne contient pas %r" % a["contient"])
    if a.get("conserve") and not any(a["conserve"] in t for t in textes_lignes):
        ecarts.append("le consolidé a perdu %r" % a["conserve"])
    return ecarts, err, cas["operations"][0].get("type", "")


EVALUATEURS = {
    "lecture": eval_lecture,
    "traduction": eval_traduction,
    "designation": eval_designation,
    "decompte": eval_decompte,
    "articles_crees": eval_articles_crees,
    "consolidation": eval_consolidation,
}

TITRES = {
    "lecture": "LIRE          ",
    "traduction": "TRADUIRE      ",
    "designation": "DÉSIGNER      ",
    "decompte": "DÉCOMPTER     ",
    "articles_crees": "ARTICLES CRÉÉS",
    "consolidation": "CONSOLIDER    ",
}


# --------------------------------------------------------------------------- exécution
def executer(adaptateur, familles, verbeux=False):
    rapport = {"familles": {}, "total": {"reussis": 0, "cas": 0}}
    for famille in familles:
        cas = charger(famille)
        fonction = getattr(adaptateur, FONCTIONS[famille], None)
        if fonction is None:
            rapport["familles"][famille] = {"couverte": False, "cas": len(cas),
                                            "reussis": 0, "echecs": []}
            print("  %s :  non couverte  (fonction %s absente de l'adaptateur)"
                  % (TITRES[famille], FONCTIONS[famille]))
            continue
        reussis, echecs = 0, []
        for c in cas:
            ecarts, err, resume = EVALUATEURS[famille](fonction, c)
            if err:
                ecarts = list(ecarts) + ["exception : " + err]
            if not ecarts:
                reussis += 1
            else:
                echecs.append({"id": c["id"], "source": c.get("source", ""),
                               "resume": resume, "ecarts": ecarts})
        rapport["familles"][famille] = {"couverte": True, "cas": len(cas),
                                        "reussis": reussis, "echecs": echecs}
        rapport["total"]["reussis"] += reussis
        rapport["total"]["cas"] += len(cas)
        print("  %s : %3d / %3d" % (TITRES[famille], reussis, len(cas)))
        if verbeux:
            for e in echecs:
                print("\n    ÉCHEC %s  [%s]" % (e["id"], e["source"]))
                print("      %s" % e["resume"])
                for x in e["ecarts"]:
                    print("        · " + x)
            if echecs:
                print("")
    return rapport


def main():
    ap = argparse.ArgumentParser(description="Banc de légistique")
    ap.add_argument("--adaptateur", required=True,
                    help="chemin d'un fichier .py ou nom d'un module importable")
    ap.add_argument("--famille", action="append", choices=FAMILLES,
                    help="n'exécuter que cette famille (répétable)")
    ap.add_argument("-v", "--verbeux", action="store_true",
                    help="détailler chaque échec")
    ap.add_argument("--json", dest="sortie_json",
                    help="écrire le rapport détaillé dans ce fichier")
    args = ap.parse_args()

    adaptateur = charger_adaptateur(args.adaptateur)
    familles = args.famille or list(FAMILLES)

    print("=== BANC DE LÉGISTIQUE ===")
    print("    adaptateur : %s\n" % args.adaptateur)
    rapport = executer(adaptateur, familles, args.verbeux)
    t = rapport["total"]
    couvertes = [f for f in familles if rapport["familles"][f]["couverte"]]
    print("\n  TOTAL          : %3d / %3d  (%d famille%s couverte%s sur %d)"
          % (t["reussis"], t["cas"], len(couvertes),
             "s" if len(couvertes) > 1 else "", "s" if len(couvertes) > 1 else "",
             len(familles)))
    if not args.verbeux and t["reussis"] < t["cas"]:
        print("  (relancer avec -v pour le détail des échecs)")

    if args.sortie_json:
        with open(args.sortie_json, "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=1)
        print("  rapport écrit dans %s" % args.sortie_json)

    return 0 if t["reussis"] == t["cas"] else 1


if __name__ == "__main__":
    sys.exit(main())
