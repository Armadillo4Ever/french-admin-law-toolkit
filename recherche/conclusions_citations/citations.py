# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Armadillo4Ever
"""Retrouver les conclusions des rapporteurs publics à partir de la jurisprudence, en trois rangs.

Constat de départ : chercher directement « dans les conclusions » par similarité de sens donne de mauvais
résultats. Une conclusion est un texte long, argumentatif, qui parle de tout ; ses passages se ressemblent.
La recherche dans la jurisprudence fichée, elle, est fiable. On part donc des décisions trouvées :

  rang 1  les conclusions PRONONCÉES SUR ces décisions (même numéro de requête : aucune recherche floue) ;
  rang 2  les conclusions ULTÉRIEURES qui CITENT ces décisions : c'est là que se lit la portée d'une
          décision de principe, et pour une décision sans conclusions publiées, c'est la seule entrée ;
  rang 3  la recherche directe, gardée pour l'analogie quand aucune décision ne domine.

Ce module fournit l'index des citations (rang 2) et l'assemblage des trois rangs. Il ne dépend d'aucun
moteur : on lui passe les numéros des décisions trouvées et, si l'on veut le rang 3, une fonction de
recherche directe. Bibliothèque standard uniquement.

Format d'entrée de l'index : une suite de passages (id_passage, numero_de_la_conclusion, texte).
"""
import re

# « n° 387763 », « nos 387763, 387764 et 387765 », « req. n° 387763 » ; numéros de 5 ou 6 chiffres.
# La forme « n° » est exigée : sans elle, on ramasse des dates, des montants et des numéros d'articles.
RE_BLOC = re.compile(r"\bn(?:°|º|o|os|°s)\s*\.?\s*((?:\d{5,6}(?!\d))(?:\s*(?:,|et|&)\s*\d{5,6}(?!\d))*)", re.I)
RE_NUM = re.compile(r"(?<!\d)\d{5,6}(?!\d)")


def numeros_cites(texte, propre=None):
    """Numéros de requête cités dans un texte, dans l'ordre, sans doublon, hors le numéro propre."""
    vus = []
    for b in RE_BLOC.finditer(texte or ""):
        for c in RE_NUM.findall(b.group(1)):
            if c != propre and c not in vus:
                vus.append(c)
    return vus


def construire_index(passages):
    """passages : itérable de (id_passage, numero_conclusion, texte).
    Rend {"propres": numero -> [id_passage], "citations": numero cité -> [id_passage]}."""
    propres, citations = {}, {}
    for pid, num, texte in passages:
        num = str(num or "")
        propres.setdefault(num, []).append(pid)
        for c in numeros_cites(texte, num):
            citations.setdefault(c, []).append(pid)
    return {"propres": propres, "citations": citations}


def extrait_centre(texte, numero, largeur=700):
    """Passage centré sur la mention du numéro : c'est là que la décision est discutée."""
    i = (texte or "").find(numero)
    if i < 0:
        return (texte or "")[:largeur]
    a = max(0, i - largeur // 2)
    return texte[a:a + largeur]


def trois_rangs(decisions, index, k=8, par_decision=3, n_decisions_citees=5, directe=None, meilleur=None, texte=None):
    """decisions : numéros des décisions trouvées par la recherche jurisprudentielle, dans l'ordre.
    directe(k) -> [id_passage] : recherche directe facultative (rang 3).
    meilleur(ids) -> id : choisit, parmi plusieurs passages d'une même conclusion, le plus proche de la
    question (par défaut le premier).
    texte(id) -> str : facultatif ; s'il est fourni, un passage dont le début a déjà été rendu est écarté.
    Les affaires jointes ou en série portent souvent des conclusions identiques sous plusieurs numéros :
    sans ce filtre, le même texte occupe plusieurs places de la liste.
    Rend une liste de dicts {rang, motif, numero, passage}. Une place est réservée au rang 3 si k >= 4."""
    meilleur = meilleur or (lambda ids: ids[0])
    out, vus, debuts = [], set(), set()

    def neuf(p):
        if p in vus:
            return False
        if texte is not None:
            debut = " ".join((texte(p) or "").split())[:160]
            if debut and debut in debuts:
                return False
            debuts.add(debut)
        vus.add(p)
        return True
    place3 = 1 if (directe and k >= 4) else 0
    for n in decisions:
        if len(out) >= k - place3:
            break
        ids = index["propres"].get(n)
        if ids:
            p = meilleur(ids)
            if neuf(p):
                out.append({"rang": 1, "motif": "conclusions prononcées sur la décision n° %s" % n, "numero": n, "passage": p})
    for n in decisions[:n_decisions_citees]:
        for p in (index["citations"].get(n) or [])[:par_decision]:
            if len(out) >= k - place3:
                break
            if neuf(p):
                out.append({"rang": 2, "motif": "conclusions ultérieures citant la décision n° %s" % n, "numero": n, "passage": p})
    if directe:
        for p in directe(k):
            if len(out) >= k:
                break
            if neuf(p):
                out.append({"rang": 3, "motif": "recherche directe dans les conclusions", "numero": None, "passage": p})
    return out


if __name__ == "__main__":
    t = "Vous avez jugé, par votre décision d'Assemblée du 13 juillet 2016 (n° 387763), puis nos 401234 et 401235..."
    print(numeros_cites(t))
    idx = construire_index([("a1", "400000", t), ("b1", "387763", "conclusions sur Czabaj")])
    print(trois_rangs(["387763"], idx, k=4))
    # deux affaires jointes, mêmes conclusions : la seconde est écartée
    textes = {"a1": t, "b1": "conclusions sur Czabaj", "c1": "conclusions sur Czabaj"}
    idx = construire_index([(p, n, textes[p]) for p, n in (("a1", "400000"), ("b1", "387763"), ("c1", "387764"))])
    print(trois_rangs(["387763", "387764"], idx, k=4, texte=textes.get))
