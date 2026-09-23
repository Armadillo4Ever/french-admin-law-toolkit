# Format of the inputs and of the benchmark produced

## Input 1: the analyses (required)

A JSONL file, one analysis per line. Only four fields are read:

```json
{"numero": "412542",
 "date": "2018-06-27",
 "classement": "A",
 "abrege": "54-07-02\nPROCÉDURE. POUVOIRS ET DEVOIRS DU JUGE.\n\nOffice du juge saisi de … - Existence.\n\n1) Il résulte des articles …"}
```

| field | role |
|---|---|
| `numero` | identifier of the decision analysed; this is the expected answer |
| `abrege` | the text of the analysis (*abrégé*, abstract), blocks separated by an empty line |
| `classement` | publication level (A, B, C, and so on); used to stratify the sampling |
| `date` | used to stratify the sampling by decade |

The structure of the `abrege` matters: the first block is the code and the path
in the classification scheme, the following ones carry the classification
heading (*titrage*) and then the summary (*résumé*). The split is made on empty
lines. An abstract of a single block is discarded.

How the program chooses the statement, block by block:

1. the classification scheme path is discarded (more than 55 % capitals): it
   states no question of law, only a heading, and keeping it would amount to
   measuring a match of nomenclature;
2. a block of fewer than 60 or more than 700 characters is discarded, as is a
   block of fewer than ten words;
3. a block that starts with `1)` or contains fewer than two dashes is taken to
   be a summary; otherwise, it is the classification heading, and it is kept
   (`genre: titrage`);
4. failing a usable classification heading, the first summary makes an
   acceptable statement, closer to the words of the decision. It is kept and
   flagged (`genre: resume`), so that the two can be measured separately: a
   summary is an easier question than a classification heading.

## Input 2: the available decisions (optional but recommended)

A JSONL file of the decisions that your corpus actually contains in full text.
Only `numero` (or, failing that, `id`) is read:

```json
{"numero": "412542"}
```

A decision absent from the corpus queried would be unfindable: keeping it would
bias the measure downwards. Without this filter, all analyses are candidates,
and the figures must be read with that reservation.

The option can be repeated, to accumulate several publication levels:

```
python3 construire_banc.py --analyses analyses.jsonl \
    --decisions decisions_A_ids.jsonl --decisions decisions_B_ids.jsonl
```

## Output: the benchmark

```json
{"id": "f001",
 "office": "contentieux",
 "cible": "decisions",
 "question": "Office du juge saisi de conclusions à fin d'injonction - …",
 "attendus": [{"cle": "412542", "note": 2}],
 "_niveau": "A", "_date": "2018-06-27", "_genre": "titrage"}
```

| field | role |
|---|---|
| `question` | the statement of the point of law, as a judge wrote it |
| `attendus` | the judged sources (expected results); `note` 2 = leading source, 1 = useful supporting source |
| `cible` | the corpus to query. `decisions` forbids querying the analyses |
| `_niveau`, `_date`, `_genre` | diagnostic fields, never evaluated |

This format is the one expected by [`../mesurer.py`](../mesurer.py). A
hand-written benchmark conforms to it without difficulty: all it takes is a
question and a list of expected results.

## Where to find analyses

The decisions of the administrative courts and their analyses are published in
open data on [data.gouv.fr](https://www.data.gouv.fr/) and through the
[Judilibre](https://www.data.gouv.fr/dataservices/api-judilibre/) API. The exact
format of these sources is not the one expected here: they must be converted to
JSONL with the four fields above, which takes a few lines. The benchmark does
not provide this converter, because it depends on the version of the dataset you
download.

The files `exemple_analyses.jsonl` and `exemple_decisions.jsonl` are
**illustrations of the format**, written for this repository: neither the
numbers nor the analyses refer to real decisions.
