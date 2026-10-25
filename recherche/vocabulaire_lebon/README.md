# Rejoindre le vocabulaire du Recueil Lebon ancien

Le Recueil Lebon de 1840 à 1960, numérisé par la BnF sur Gallica, parle une autre langue que la nôtre. On
n'y trouve pas de « rapporteur public » mais un « commissaire du gouvernement », pas de « tribunal
administratif » mais un « conseil de préfecture », pas de « permis de construire » mais un « permis de
bâtir », pas de « taxe foncière » mais une « contribution foncière ». Une question posée en vocabulaire
d'aujourd'hui passe à côté des décisions qui ont fondé la matière.

[`correspondances.json`](correspondances.json) est un répertoire de 71 entrées : pour chaque notion
contemporaine, les termes anciens qui la recouvrent ou l'approchent. Il couvre la procédure contentieuse,
la responsabilité, la fonction publique, la police, les libertés, l'urbanisme et la voirie, les contrats et
concessions, les collectivités, la fiscalité directe, l'assistance et la santé, les étrangers, les
élections.

[`elargir.py`](elargir.py) détecte ces notions dans une question (sans accents ni casse, pluriel simple
compris) et rend les termes anciens à ajouter :

```
$ python3 elargir.py "rapporteur public et tribunal administratif, taxe foncière"
rapporteur public et tribunal administratif, taxe foncière ; commissaire du gouvernement ;
conseil de préfecture ; conseil de préfecture interdépartemental ; contribution foncière ; impôt foncier
```

## Comment s'en servir

La question d'origine n'est jamais remplacée. Dans une recherche vectorielle, on vectorise la question et
la question élargie, puis on combine les deux vecteurs ; dans une recherche plein texte, on ajoute les
termes anciens en disjonction.

Le répertoire sert surtout si l'on cherche dans le **fichage** (le sommaire et la rubrique de classement
au recueil) plutôt que dans le texte lu par reconnaissance de caractères : le fichage est court et rédigé
dans le vocabulaire de classement de l'époque, que le répertoire vise précisément ; le texte océrisé est
long et bruité.

## Limites

Ce sont des pistes de recherche, non des équivalences juridiques. « Conseil de préfecture » n'est pas
« tribunal administratif » : la compétence, la procédure et l'office ont changé. Le répertoire aide à
trouver la décision ; il ne dit rien de sa portée actuelle, qui reste à vérifier, notamment au regard des
revirements.

Il est incomplet par nature. Une entrée qui vous a manqué est une contribution utile.
