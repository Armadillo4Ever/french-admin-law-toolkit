# -*- coding: utf-8 -*-
"""Gabarit d'adaptateur pour le banc de légistique.

Copiez ce fichier, remplissez les fonctions qui vous intéressent, puis :

    python3 executer.py --adaptateur mon_adaptateur.py -v

Une fonction que vous laissez absente rend sa famille « non couverte » : elle
n'est ni comptée en réussite, ni comptée en échec. Vous pouvez donc commencer
par une seule famille.

Le format exact des entrées et des sorties est décrit dans FORMAT.md.
"""


# --------------------------------------------------------------------------- lecture
def lire(instruction):
    """Analyser une instruction de modification.

    Retourne un dictionnaire dont les clés utiles sont :
        op          l'opération, parmi les valeurs fermées listées dans FORMAT.md
        porte_sur   la nature de la portion visée : article, alinea, phrase, mots, division…
        cible       la désignation de l'endroit où l'on opère
        objet       ce que l'on y place ou retire
        ancien / nouveau / occurrence / nombre / cite_type   selon l'opération

    Le banc ne vérifie que les clés annoncées par le cas : renvoyer davantage
    de clés ne pénalise pas.
    """
    return None


# --------------------------------------------------------------------------- traduction
def traduire(instruction):
    """Rendre l'instruction sous la forme d'un nom d'opération unique.

    Retourne une chaîne (par exemple "remplacer_alinea") ou un dictionnaire
    portant la clé "type". Retourner None vaut « aucune opération », ce qui est
    la réponse attendue pour une simple annonce de modification.
    """
    return None


# --------------------------------------------------------------------------- désignation
def resoudre(article, designation):
    """Résoudre une désignation composée sur un article donné.

    article       liste de chaînes, une par ligne du texte en vigueur
    designation   par exemple "le troisième alinéa du 2° du I"

    Retourne un dictionnaire :
        alineas    [premier, dernier] rangs de ligne, en base 0 et bornes incluses
        phrase     rang de la phrase visée, le cas échéant
        position   "debut" ou "fin", le cas échéant
        inconnu    True si la désignation ne se résout pas
    """
    return None


# --------------------------------------------------------------------------- décompte
def decompter(lignes, rang_demande, regle):
    """Donner les lignes qui composent l'alinéa de rang demandé.

    lignes         liste de chaînes, une par ligne
    rang_demande   rang de l'alinéa, en base 1
    regle          "moderne" (tout retour à la ligne ouvre un alinéa) ou "ancien"

    Retourne la liste des index de lignes, en base 0, qui composent cet alinéa.
    Un tableau compte pour un seul alinéa : ses lignes sont donc rendues ensemble.
    """
    return None


# --------------------------------------------------------------------------- articles créés
def articles_crees(instruction):
    """Lister les numéros d'articles que l'instruction institue.

    Une plage désigne aussi ses éléments intermédiaires : « des articles 20-12
    à 20-14 » crée le 20-13.

    Retourne une liste ou un ensemble de chaînes ("20-12", "20-13", "20-14").
    """
    return None


# --------------------------------------------------------------------------- consolidation
def consolider(article, operations):
    """Appliquer les opérations au texte en vigueur, en gardant la trace des marques.

    article      liste de chaînes, une par ligne du texte en vigueur
    operations   liste de dictionnaires {type, designation, ancien, nouveau, …}

    Retourne un dictionnaire :
        lignes           liste de lignes ; chaque ligne est une liste de segments
                         {"e": "" | "sup" | "ajo", "t": texte}
                         "" = inchangé, "sup" = supprimé, "ajo" = ajouté
        non_appliquees   liste des opérations refusées, avec leur motif
    """
    return None
