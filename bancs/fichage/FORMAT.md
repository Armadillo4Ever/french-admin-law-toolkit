# Format des entrées et du banc produit

## Entrée 1 : les analyses (obligatoire)

Un fichier JSONL, une analyse par ligne. Seuls quatre champs sont lus :

```json
{"numero": "412542",
 "date": "2018-06-27",
 "classement": "A",
 "abrege": "54-07-02\nPROCÉDURE. POUVOIRS ET DEVOIRS DU JUGE.\n\nOffice du juge saisi de … - Existence.\n\n1) Il résulte des articles …"}
```

| champ | rôle |
|---|---|
| `numero` | identifiant de la décision analysée ; c'est la réponse attendue |
| `abrege` | le texte de l'analyse, blocs séparés par une ligne vide |
| `classement` | niveau de publication (A, B, C…) ; sert à stratifier le tirage |
| `date` | sert à stratifier le tirage par décennie |

La structure de l'`abrege` compte : le premier bloc est le code et le chemin du
plan de classement, les suivants portent le titrage puis le résumé. Le
découpage se fait sur les lignes vides. Un abrégé d'un seul bloc est écarté.

Comment le programme choisit l'énoncé, bloc par bloc :

1. le chemin du plan de classement est écarté (plus de 55 % de capitales) : il
   n'énonce aucune question de droit, seulement une rubrique, et le retenir
   reviendrait à mesurer une correspondance de nomenclature ;
2. un bloc de moins de 60 ou de plus de 700 caractères est écarté, de même
   qu'un bloc de moins de dix mots ;
3. un bloc qui commence par `1)` ou qui contient moins de deux tirets est tenu
   pour un résumé ; sinon, c'est le titrage, et il est retenu (`genre: titrage`) ;
4. à défaut de titrage exploitable, le premier résumé fait un énoncé
   acceptable, plus proche des mots de la décision. Il est retenu et signalé
   (`genre: resume`), pour pouvoir mesurer les deux séparément : un résumé est
   une question plus facile qu'un titrage.

## Entrée 2 : les décisions disponibles (facultative mais recommandée)

Un fichier JSONL des décisions que votre corpus contient réellement en texte
intégral. Seul `numero` (ou, à défaut, `id`) est lu :

```json
{"numero": "412542"}
```

Une décision absente du corpus interrogé serait introuvable : la retenir
fausserait la mesure vers le bas. Sans ce filtre, toutes les analyses sont
candidates, et les chiffres sont à lire avec cette réserve.

L'option est répétable, pour cumuler plusieurs niveaux de publication :

```
python3 construire_banc.py --analyses analyses.jsonl \
    --decisions decisions_A_ids.jsonl --decisions decisions_B_ids.jsonl
```

## Sortie : le banc

```json
{"id": "f001",
 "office": "contentieux",
 "cible": "decisions",
 "question": "Office du juge saisi de conclusions à fin d'injonction - …",
 "attendus": [{"cle": "412542", "note": 2}],
 "_niveau": "A", "_date": "2018-06-27", "_genre": "titrage"}
```

| champ | rôle |
|---|---|
| `question` | l'énoncé du point de droit, tel qu'un magistrat l'a rédigé |
| `attendus` | les sources jugées ; `note` 2 = source portante, 1 = source utile en appui |
| `cible` | le corpus à interroger. `decisions` interdit d'interroger les analyses |
| `_niveau`, `_date`, `_genre` | champs de diagnostic, jamais évalués |

Ce format est celui qu'attend [`../mesurer.py`](../mesurer.py). Un banc écrit à
la main s'y conforme sans difficulté : il suffit d'une question et d'une liste
d'attendus.

## Où trouver des analyses

Les décisions de la juridiction administrative et leurs analyses sont diffusées
en open data sur [data.gouv.fr](https://www.data.gouv.fr/) et par l'API
[Judilibre](https://www.data.gouv.fr/dataservices/api-judilibre/). Le format
exact de ces sources n'est pas celui attendu ici : il faut les convertir en
JSONL avec les quatre champs ci-dessus, ce qui tient en quelques lignes. Le
banc ne fournit pas ce convertisseur, parce qu'il dépend de la version du jeu
de données que vous téléchargez.

Les fichiers `exemple_analyses.jsonl` et `exemple_decisions.jsonl` sont des
**illustrations du format**, rédigées pour ce dépôt : ni les numéros, ni les
analyses ne renvoient à des décisions réelles.
