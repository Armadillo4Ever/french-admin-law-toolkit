# Format of the cases and adapter contract

French sources are quoted in free translation; the French text prevails. The
example records below are reproduced as they appear in the case files, in
French.

Each family is a JSONL file: one line, one case, one JSON object. All cases
carry an `id` and a `source` (the origin of the case: page of the Legislative
Drafting Guide (*Guide de légistique*), dated observation on a real text). The
source is not evaluated; it serves to trace where the requirement comes from.

The benchmark checks **only the keys declared by the case**. An answer that
carries more keys is not penalised: the benchmark does not freeze what it does
not require.

Two comparison regimes:

- fields with **closed values** (`op`, `type`, `porte_sur`, `cite_type`) are
  compared for identity. Substring tolerance would be a trap there:
  `inserer_apres` is contained in `inserer_apres_mots` and would pass for it;
- the other strings are compared after normalisation (case, spaces, apostrophes
  and quotation marks), by inclusion in one direction or the other, because a
  copied fragment may differ by a blank or a quotation mark.

---

## 1. `cas_lecture.jsonl`: reading an instruction (25 cases)

```json
{"id": "L001", "source": "guide 2026 p.437",
 "instruction": "Le troisième alinéa de l'article 6 est remplacé par les dispositions suivantes : …",
 "attendu": {"op": "remplacer", "porte_sur": "alinea", "cible": "Le troisième alinéa de l'article 6"}}
```

**Function: `lire(instruction) -> dict`**

| key | regime | what it says |
|---|---|---|
| `op` | closed | the operation |
| `porte_sur` | closed | the nature of the portion targeted |
| `cible` | text | the place where the operation is made (target) |
| `objet` | text | what is placed there or removed (object) |
| `ancien`, `nouveau` | text | the words replaced and the new words |
| `occurrence` | value | the rank of the occurrence targeted, when specified |
| `nombre` | value | the number of elements inserted |
| `cite_type` | closed | what the quotation marks cite: `mots` (words) or `references` |
| `rang_ligne`, `rangs_lignes`, `cible_par_contenu` | value | rank details |

`op` ∈ `abroger` (repeal), `ajouter_debut` (add at the beginning), `ajouter_fin`
(add at the end), `ajouter_phrase` (add a sentence), `constituer` (constitute),
`inserer_apres` (insert after), `inserer_apres_mots` (insert after the words),
`remplacer` (replace), `remplacer_debut` (replace the beginning), `renumeroter`
(renumber), `retablir` (reinstate), `supprimer` (delete).

`porte_sur` ∈ `article`, `alinea` (paragraph), `phrase` (sentence), `ligne`
(line), `division`, `subdivision`.

## 2. `cas_traduction.jsonl`: naming the operation (26 cases)

```json
{"id": "T001", "source": "guide 2026 p. 437",
 "instruction": "Le troisième alinéa de l'article 5 est remplacé par les dispositions suivantes :",
 "operation_attendue": "remplacer_alinea"}
```

**Function: `traduire(instruction) -> str | dict | None`**

Return the string, or a dictionary carrying the key `type`. `null` is an
**expected** answer for an announcement of amendment ("Article 12 is amended as
follows:"), which introduces the operations without being one.

`type` ∈ `abroger_alinea` (repeal paragraph), `ajouter_alinea` (add paragraph),
`ajouter_mots` (add words), `ajouter_phrase` (add sentence), `inserer_apres`
(insert after), `inserer_apres_mots` (insert after the words),
`inserer_apres_phrase` (insert after the sentence), `inserer_ligne_apres`
(insert line after), `remplacer_alinea` (replace paragraph), `remplacer_lignes`
(replace lines), `remplacer_mots` (replace words), `renumeroter` (renumber),
`supprimer_lignes` (delete lines).

## 3. `cas_designation.jsonl`: resolving a compound designation (19 cases)

```json
{"id": "D001", "source": "rangs simples",
 "article": ["I. - Sont applicables …", "1° Les agents des douanes ;", "…"],
 "designation": "le premier alinéa",
 "attendu": {"alineas": [0, 0]}}
```

**Function: `resoudre(article, designation) -> dict`**

`article` is the list of lines of the text in force.

| key | what it says |
|---|---|
| `alineas` | `[first, last]`, line indexes in **base 0**, bounds included |
| `phrase` | rank of the sentence targeted within the paragraph |
| `position` | `"debut"` (beginning) or `"fin"` (end) |
| `inconnu` | `true` when the designation cannot be resolved on this article |

Designations are composable and are read from the widest container to the
finest portion: "the third paragraph of 2° of I". A level runs to the next
marker of the same level: the unmarked paragraphs that follow a `2°` belong to
it.

## 4. `cas_decompte.jsonl`: counting the paragraphs (6 cases)

```json
{"id": "C001", "source": "guide 2026 p. 411 — un tableau = un alinéa",
 "lignes": ["I. - …", "| Dispositions | Rédaction |", "| Article L. 511-3 | … |", "…"],
 "rang_demande": 2, "regle": "moderne", "lignes_attendues": [1, 3]}
```

**Function: `decompter(lignes, rang_demande, regle) -> list[int]`**

Return the line indexes, in base 0, that make up the paragraph of the requested
rank (base 1). A table constitutes **a single paragraph**, whatever the number
of its rows: they are therefore returned together.

`regle` is `moderne` (every line break opens a paragraph, circular of
20 October 2000, NOR PRMX0004462C) or `ancien` (a paragraph opens only after a
full stop). The modern count also applies to texts prior to 2000; the `ancien`
cases serve to check that an implementation offering both counts does not
confuse them.

## 5. `cas_articles_crees.jsonl`: the articles that the text creates (3 cases)

```json
{"id": "X001", "source": "dossier ECOC2616776X, 01/09/2026 (plage)",
 "instruction": "Le titre Ier est complété par des articles 20-12 à 20-14 ainsi rédigés :",
 "articles_crees": ["20-12", "20-13", "20-14"]}
```

**Function: `articles_crees(instruction) -> list[str] | set[str]`**

Order is irrelevant; the comparison is made on the sets. A range also
designates its intermediate elements: "articles 20-12 to 20-14" creates 20-13.
Few cases, but the trap is costly: an article created by the text does not
exist in the law in force, and looking it up leads to declaring it not found.

## 6. `cas_consolidation.jsonl`: applying at the right place (10 cases)

```json
{"id": "S001", "source": "phrase ajoutée au dernier alinéa du I",
 "article": ["I. - Les dispositions …", "1° …", "2° …", "Un décret …", "II. - …"],
 "operations": [{"type": "ajouter_phrase", "designation": "Le dernier alinéa du I",
                 "nouveau": "Ce décret est pris après avis de l'Autorité de régulation."}],
 "attendu": {"apres_alinea": 3, "marque": "ajo", "texte": "Ce décret est pris …"}}
```

**Function: `consolider(article, operations) -> dict`**

Return:

```json
{"lignes": [[{"e": "", "t": "texte inchangé"},
             {"e": "ajo", "t": " phrase ajoutée"}],
            [{"e": "sup", "t": "alinéa supprimé"}]],
 "non_appliquees": [{"type": "…", "motif": "…"}]}
```

A line is a list of segments; `e` is `""` (unchanged), `"sup"` (deleted) or
`"ajo"` (added). This segmentation is what makes it possible to render a
consolidated text with tracked changes.

What the benchmark checks, according to the keys of the case:

| key of `attendu` | check |
|---|---|
| `refusee` | the operation was expected to appear in `non_appliquees` |
| `aucun_barre` | no `sup` segment in the consolidated text |
| `barre` | this text is struck through |
| `texte` | this text is added |
| `position` | rank of the added segment among all segments |
| `apres_alinea` | the text is **within** the line of this index, not in a separate line |
| `ligne_touchee` | the expected mark bears on this precise line |
| `contient` | the consolidated text contains this text |
| `conserve` | the consolidated text has not lost this text |

`apres_alinea` is the most discriminating case: a sentence added to a paragraph
stays in that paragraph; it does not become a separate paragraph.
