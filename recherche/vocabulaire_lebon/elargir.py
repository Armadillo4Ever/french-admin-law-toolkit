# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Armadillo4Ever
"""Élargit une question rédigée en vocabulaire contemporain aux termes du Recueil Lebon ancien.

    >>> from elargir import elargir
    >>> elargir("refus de permis de construire pour non-respect du plan local d'urbanisme")
    ['permis de bâtir', 'alignement', 'autorisation de bâtir', "plan d'aménagement", ...]

La détection ignore accents, casse et ponctuation, et accepte le pluriel simple en « s ». Les termes
ajoutés servent à composer une seconde requête (ou à enrichir la première) ; ils ne remplacent jamais
la question d'origine. Bibliothèque standard uniquement.
"""
import json
import os
import re
import unicodedata

_ICI = os.path.dirname(os.path.abspath(__file__))


def normaliser(s):
    t = "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]", " ", t)).strip()


def charger(chemin=None):
    d = json.load(open(chemin or os.path.join(_ICI, "correspondances.json"), encoding="utf-8"))
    return [(tuple(normaliser(m) for m in e["moderne"]), tuple(e["ancien"])) for e in d["entrees"]]


_TABLE = None


def elargir(question, table=None):
    """Liste ordonnée, sans doublon, des termes anciens correspondant aux notions de la question."""
    global _TABLE
    if table is None:
        if _TABLE is None:
            _TABLE = charger()
        table = _TABLE
    q = " " + normaliser(question) + " "
    ajout = []
    for modernes, anciens in table:
        if any((" " + m + " ") in q or (" " + m + "s ") in q for m in modernes):
            for a in anciens:
                if a not in ajout:
                    ajout.append(a)
    return ajout


def requete_elargie(question, table=None):
    """La question suivie des termes anciens, prête à être vectorisée ou passée à un moteur plein texte."""
    ajout = elargir(question, table)
    return question if not ajout else question + " ; " + " ; ".join(ajout)


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "refus de permis de construire pour non-respect du plan local d'urbanisme"
    print(requete_elargie(q))
