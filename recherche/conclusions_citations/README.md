# Conclusions des rapporteurs publics : partir de la jurisprudence

## Le problème

Chercher directement « dans les conclusions » par similarité de sens déçoit. Une conclusion est un texte
long et argumentatif, qui parcourt le litige entier ; découpée en passages, elle produit des milliers de
fragments qui se ressemblent tous un peu. Sur une question aussi classique que le délai raisonnable d'un an
pour contester une décision dépourvue de la mention des voies et délais de recours, la recherche directe ne
faisait remonter ni les conclusions prononcées sur la décision de principe, ni celles qui la discutent
ensuite.

La recherche dans la jurisprudence fichée, elle, est fiable : le fichage est un résumé rédigé par un
magistrat, dense, sans bruit.

## La méthode, en trois rangs

1. **Les conclusions prononcées sur les décisions trouvées.** La recherche jurisprudentielle rend des
   numéros de requête ; les conclusions portent le même numéro. Le rapprochement est exact, aucune
   recherche floue n'intervient. Parmi les passages de cette conclusion, on rend le plus proche de la
   question.
2. **Les conclusions ultérieures qui citent ces décisions.** Un index, construit une fois, associe à chaque
   numéro de requête les passages d'autres conclusions qui le citent (« n° 387763 », « nos 401234 et
   401235 »). L'extrait rendu est centré sur la mention : c'est là que la décision est discutée, appliquée,
   nuancée. C'est souvent le rang le plus utile pour une décision de principe ; et pour une décision
   ancienne, sans conclusions publiées, c'est la seule entrée.
3. **La recherche directe**, conservée pour l'analogie quand aucune décision ne domine. Une place lui est
   réservée.

C'est la manière dont un juge cherche : d'abord la décision, puis ce qu'on en a dit.

## Ce que donne la mesure

Sur 135 questions dont la décision attendue est connue, en comptant les cinq premiers résultats :

| | avant (recherche directe) | après (trois rangs) |
|---|---|---|
| conclusions prononcées sur la décision attendue (33 questions où elles existent) | 0 / 33 | 31 / 33 |
| au moins une conclusion qui cite la décision attendue (125 questions) | 0 / 125 | 89 / 125 |
| l'un ou l'autre | 0 / 135 | 104 / 135 |

Le temps de réponse médian passe de 2,1 à 3,1 secondes, parce que la recherche jurisprudentielle est
désormais lancée en premier.

Ces chiffres comparent deux configurations sur le même banc ; ils ne mesurent pas une qualité absolue.

## Le module

[`citations.py`](citations.py), bibliothèque standard uniquement :

- `numeros_cites(texte, propre)` : les numéros de requête cités dans un texte ;
- `construire_index(passages)` : l'index « propres » et « citations » à partir de
  `(id_passage, numéro_de_la_conclusion, texte)` ;
- `extrait_centre(texte, numero)` : le passage où la décision est discutée ;
- `trois_rangs(decisions, index, k, directe=..., texte=...)` : l'assemblage, à partir des numéros que rend
  votre propre recherche jurisprudentielle.

## Trois précautions

- **Exiger la forme « n° ».** Sans elle, l'expression régulière ramasse des dates, des montants, des
  numéros d'articles ou de pages, et l'index se remplit de fausses citations.
- **Reconstruire l'index à chaque mise à jour du fonds.** Un index décalé d'une ligne rend des passages
  qui ne correspondent plus aux références affichées ; il vaut mieux revenir à la recherche directe que
  rendre un résultat faux. Une signature du fichier source (taille et date) suffit à le détecter.
- **Écarter les conclusions identiques.** Dans les affaires jointes ou en série, les mêmes conclusions
  figurent sous plusieurs numéros. Passez `texte=` à `trois_rangs` : un passage dont le début a déjà été
  rendu est écarté, et la place revient à une autre conclusion.
