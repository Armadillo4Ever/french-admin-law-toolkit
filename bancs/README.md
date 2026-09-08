# Bancs d'essai

Deux bancs, et un harnais de mesure commun. Tous en bibliothèque standard, sans
dépendance, sans réseau, sans modèle.

| dossier | ce qu'il mesure |
|---|---|
| [`fichage/`](fichage/) | une recherche juridique retrouve-t-elle la décision qui a posé la règle ? |
| [`legistique/`](legistique/) | une instruction de modification d'un texte est-elle lue et appliquée correctement ? |

[`mesurer.py`](mesurer.py) est le harnais de mesure des bancs de recherche
(nDCG@10, rappel, MRR, rang du premier attendu, résultats par fonds). Il appelle
votre moteur à travers un adaptateur : voyez
[`adaptateur_recherche_gabarit.py`](adaptateur_recherche_gabarit.py).

Le banc de légistique a son propre exécuteur,
[`legistique/executer.py`](legistique/executer.py), parce qu'il ne mesure pas un
classement mais une analyse.

## Le principe commun

Les deux bancs sont bâtis sur la même conviction : **un banc utile est un banc
qui a fait échouer quelque chose.** Aucun cas n'est là pour faire nombre. Le banc
de légistique est une collection de fautes constatées, chacune avec sa source. Le
banc de fichage exploite une annotation qui existait déjà, plutôt que d'en
fabriquer une nouvelle.

Et le corollaire : **les chiffres servent à comparer deux configurations sur le
même banc, jamais à mesurer une qualité absolue.** Les jugements de pertinence
sont incomplets par construction, les cas ne sont pas un échantillon
représentatif. Un score n'a de sens que rapporté à un autre score obtenu dans les
mêmes conditions.
