# -*- coding: utf-8 -*-
"""Gabarit d'adaptateur pour mesurer.py.

Copiez ce fichier, branchez votre moteur dans chercher(), puis :

    python3 mesurer.py --banc fichage/banc_fichage.jsonl --adaptateur mon_moteur.py
"""


def chercher(question, k=10, fonds=None):
    """Interroger votre moteur et rendre ses résultats.

    question   l'énoncé, tel qu'il figure dans le banc
    k          nombre de résultats souhaités par fonds
    fonds      liste de fonds à interroger, ou None pour tous. Un banc construit à
               partir du fichage porte `cible: decisions` : n'interrogez alors que le
               texte intégral des décisions, sans quoi la mesure est faussée par la
               présence de la question elle-même dans le corpus des analyses.

    Retourne {"nom du fonds": [document, ...]} — ou une simple liste de documents,
    traitée comme un fonds unique.

    Un document est un dictionnaire quelconque. Le banc y cherche lui-même les
    identifiants : numéro de décision, LEGIARTI, CELEX, numéro de pourvoi, requête
    CEDH, article de code, numéro de loi ou de décret, dans les champs d'identifiant
    usuels, dans `liens`, et dans les textes de référence. Vous n'avez donc rien à
    normaliser : rendez vos résultats tels quels, dans l'ordre du moteur.
    """
    return {}
