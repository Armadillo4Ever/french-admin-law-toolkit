# Banc de fichage : mesurer une recherche juridique sans annoter une seule question

## L'idée

Le fichage de la jurisprudence est une ressource d'évaluation que personne
n'utilise comme telle. Chaque analyse associe **un point de droit rédigé par un
magistrat** à **la décision qui l'a posé**. C'est exactement un couple
question-réponse, produit par un expert, sur le fond du droit. Il y en a des
dizaines de milliers, et ils sont publics.

Un banc d'évaluation coûte cher parce qu'il faut annoter : poser des questions,
puis juger, pour chacune, quelles sources sont pertinentes. Ici, le jugement
existe déjà. Il suffit de le retourner : on donne l'énoncé du point de droit au
moteur, et on regarde s'il retrouve la décision.

```
python3 construire_banc.py --analyses analyses.jsonl --decisions decisions_ids.jsonl -n 300
python3 ../mesurer.py --banc banc_fichage.jsonl --adaptateur mon_moteur.py --sortie avant.json
python3 ../mesurer.py --comparer avant.json apres.json
```

Bibliothèque standard uniquement. Ni modèle, ni service, ni réseau : le banc se
construit hors ligne, à partir de vos fichiers. Le format des entrées est décrit
dans [FORMAT.md](FORMAT.md).

Pour voir tourner la chaîne sans rien préparer, deux fichiers d'exemple
illustrent le format attendu :

```
python3 construire_banc.py --analyses exemple_analyses.jsonl \
    --decisions exemple_decisions.jsonl -n 5 --sortie essai.jsonl
```

## Ce que le banc mesure, et ce qu'il ne mesure pas

Il mesure la recherche **« je cherche LA bonne réponse »** : partant de l'énoncé
d'une règle, le moteur retrouve-t-il la décision qui l'a posée ?

Il ne mesure **pas** la recherche par analogie, qui est l'autre moitié du
métier : quand la question est nouvelle, on raisonne sur un faisceau d'appuis
dont aucun ne répond exactement, et la mesure qui compte est alors le rappel sur
un faisceau jugé à la main. Ce banc-là ne se fabrique pas tout seul.

Il ne mesure pas non plus la qualité de la rédaction produite à partir des
sources trouvées.

## Les trois précautions qui font la validité du banc

**1. Pas de fuite.** La question étant tirée d'une analyse, interroger le corpus
des analyses la retrouverait telle quelle, et la mesure serait nulle. Chaque
question porte donc `"cible": "decisions"` : seul le texte intégral des décisions
doit être interrogé. C'est la précaution la plus facile à oublier et la seule qui
invalide tout.

**2. Pas de question introuvable.** Une décision absente du corpus interrogé ne
peut pas être retrouvée : la retenir mesurerait la couverture du corpus, pas la
qualité de la recherche. D'où le second fichier d'entrée, qui restreint le tirage
aux décisions réellement disponibles en texte intégral.

**3. Pas de chemin de classement.** Le premier bloc d'un abrégé est une rubrique
du plan de classement, rédigée en capitales. Le prendre pour une question
reviendrait à mesurer une correspondance de nomenclature. Il est écarté, ce qui
écarte aussi les fichages anciens qui s'y réduisent : le banc penche donc vers
les décisions récentes. C'est un biais assumé, préférable à des questions vides
de sens.

## Le tirage

Sans précaution, un tirage aléatoire produit un banc massivement composé de
décisions récentes du niveau de publication le plus fourni. Le tirage est donc
**stratifié par niveau de classement et par décennie**, et **reproductible** :
même graine, même banc, d'une exécution à l'autre et d'une machine à l'autre.
C'est ce qui permet de comparer deux configurations d'un moteur sans que le banc
bouge sous les pieds.

Le programme affiche la répartition obtenue. Regardez-la : elle dit ce que votre
chiffre global mesure vraiment.

## Lire les chiffres

`../mesurer.py` rend, pour chaque question et en moyenne :

| mesure | ce qu'elle dit |
|---|---|
| part de questions où au moins un attendu est trouvé | le taux d'échec franc |
| nDCG@10 | l'attendu est-il **haut** dans la liste, ou noyé au rang 40 ? |
| rappel@50 | quelle part des attendus est retrouvée, à profondeur donnée |
| MRR | l'inverse du rang du premier attendu, moyenné |
| rang médian du premier attendu | le chiffre que ressent celui qui cherche |

Le rapport détaille aussi, par fonds, quels attendus ont été rendus et à quel
rang **dans ce fonds** : sur une recherche multi-fonds, l'ordre entre fonds est
une convention d'affichage, et le rang à l'intérieur d'un fonds est ce que voit
l'œil.

**Ce que ces chiffres valent.** Les jugements de pertinence sont incomplets par
construction : une décision excellente que l'analyse ne cite pas compte ici comme
non pertinente et pénalise injustement le moteur. Ces chiffres servent à
**comparer deux configurations sur le même banc, avec le même `k`**. Ils ne
mesurent pas une qualité absolue, et deux bancs différents ne se comparent pas.

## Transposer

Rien dans la méthode n'est propre à la juridiction administrative. Il faut
seulement un corpus où quelqu'un a déjà écrit, à côté de chaque document, ce
que ce document apporte : sommaires de la Cour de cassation, résumés
jurisprudentiels de la Cour de justice, notices d'arrêts de la Cour européenne
des droits de l'homme, mais aussi, hors du droit, tout corpus documentaire
indexé par des professionnels. La question à se poser est toujours la même :
**l'annotation existe-t-elle déjà, sous une autre forme, dans les données ?**
