# Format des cas et contrat de l'adaptateur

Chaque famille est un fichier JSONL : une ligne, un cas, un objet JSON. Tous les
cas portent un `id` et une `source` (l'origine du cas : page du guide de
légistique, observation datée sur un texte réel). La source n'est pas évaluée,
elle sert à retrouver d'où vient l'exigence.

Le banc ne vérifie **que les clés annoncées par le cas**. Une réponse qui porte
davantage de clés n'est pas pénalisée : le banc ne fige pas ce qu'il n'exige pas.

Deux régimes de comparaison :

- les champs à **valeurs fermées** (`op`, `type`, `porte_sur`, `cite_type`) se
  comparent à l'identique. La tolérance de sous-chaîne y serait un piège :
  `inserer_apres` est contenu dans `inserer_apres_mots` et passerait pour lui ;
- les autres chaînes se comparent après normalisation (casse, espaces,
  apostrophes et guillemets), par inclusion dans un sens ou dans l'autre, parce
  qu'un fragment recopié peut différer d'un blanc ou d'un guillemet.

---

## 1. `cas_lecture.jsonl` — lire une instruction (25 cas)

```json
{"id": "L001", "source": "guide 2026 p.437",
 "instruction": "Le troisième alinéa de l'article 6 est remplacé par les dispositions suivantes : …",
 "attendu": {"op": "remplacer", "porte_sur": "alinea", "cible": "Le troisième alinéa de l'article 6"}}
```

**Fonction : `lire(instruction) -> dict`**

| clé | régime | ce qu'elle dit |
|---|---|---|
| `op` | fermé | l'opération |
| `porte_sur` | fermé | la nature de la portion visée |
| `cible` | texte | l'endroit où l'on opère |
| `objet` | texte | ce que l'on y place ou retire |
| `ancien`, `nouveau` | texte | les mots remplacés et les mots nouveaux |
| `occurrence` | valeur | le rang de l'occurrence visée, quand il est précisé |
| `nombre` | valeur | le nombre d'éléments insérés |
| `cite_type` | fermé | ce que citent les guillemets : `mots` ou `references` |
| `rang_ligne`, `rangs_lignes`, `cible_par_contenu` | valeur | précisions de rang |

`op` ∈ `abroger`, `ajouter_debut`, `ajouter_fin`, `ajouter_phrase`,
`constituer`, `inserer_apres`, `inserer_apres_mots`, `remplacer`,
`remplacer_debut`, `renumeroter`, `retablir`, `supprimer`.

`porte_sur` ∈ `article`, `alinea`, `phrase`, `ligne`, `division`, `subdivision`.

## 2. `cas_traduction.jsonl` — nommer l'opération (26 cas)

```json
{"id": "T001", "source": "guide 2026 p. 437",
 "instruction": "Le troisième alinéa de l'article 5 est remplacé par les dispositions suivantes :",
 "operation_attendue": "remplacer_alinea"}
```

**Fonction : `traduire(instruction) -> str | dict | None`**

Retourner la chaîne, ou un dictionnaire portant la clé `type`. `null` est une
réponse **attendue** pour une annonce de modification (« L'article 12 est ainsi
modifié : »), qui introduit les opérations sans en être une.

`type` ∈ `abroger_alinea`, `ajouter_alinea`, `ajouter_mots`, `ajouter_phrase`,
`inserer_apres`, `inserer_apres_mots`, `inserer_apres_phrase`,
`inserer_ligne_apres`, `remplacer_alinea`, `remplacer_lignes`,
`remplacer_mots`, `renumeroter`, `supprimer_lignes`.

## 3. `cas_designation.jsonl` — résoudre une désignation composée (19 cas)

```json
{"id": "D001", "source": "rangs simples",
 "article": ["I. - Sont applicables …", "1° Les agents des douanes ;", "…"],
 "designation": "le premier alinéa",
 "attendu": {"alineas": [0, 0]}}
```

**Fonction : `resoudre(article, designation) -> dict`**

`article` est la liste des lignes du texte en vigueur.

| clé | ce qu'elle dit |
|---|---|
| `alineas` | `[premier, dernier]`, index de lignes en **base 0**, bornes incluses |
| `phrase` | rang de la phrase visée à l'intérieur de l'alinéa |
| `position` | `"debut"` ou `"fin"` |
| `inconnu` | `true` quand la désignation ne se résout pas sur cet article |

Les désignations sont composables et se lisent du support le plus large à la
portion la plus fine : « le troisième alinéa du 2° du I ». Un degré court
jusqu'au marqueur suivant de même niveau : les alinéas non marqués qui suivent
un `2°` lui appartiennent.

## 4. `cas_decompte.jsonl` — décompter les alinéas (6 cas)

```json
{"id": "C001", "source": "guide 2026 p. 411 — un tableau = un alinéa",
 "lignes": ["I. - …", "| Dispositions | Rédaction |", "| Article L. 511-3 | … |", "…"],
 "rang_demande": 2, "regle": "moderne", "lignes_attendues": [1, 3]}
```

**Fonction : `decompter(lignes, rang_demande, regle) -> list[int]`**

Retourner les index de lignes, en base 0, qui composent l'alinéa de rang
demandé (base 1). Un tableau constitue **un seul alinéa**, quel que soit le
nombre de ses lignes : elles sont donc rendues ensemble.

`regle` vaut `moderne` (tout retour à la ligne ouvre un alinéa, circulaire du
20 octobre 2000, NOR PRMX0004462C) ou `ancien` (l'alinéa ne s'ouvre qu'après un
point). Le décompte moderne s'applique aussi aux textes antérieurs à 2000 ; les
cas `ancien` servent à vérifier qu'une implémentation qui offre les deux
décomptes ne les confond pas.

## 5. `cas_articles_crees.jsonl` — les articles que le texte institue (3 cas)

```json
{"id": "X001", "source": "dossier ECOC2616776X, 01/09/2026 (plage)",
 "instruction": "Le titre Ier est complété par des articles 20-12 à 20-14 ainsi rédigés :",
 "articles_crees": ["20-12", "20-13", "20-14"]}
```

**Fonction : `articles_crees(instruction) -> list[str] | set[str]`**

L'ordre est indifférent, la comparaison se fait sur les ensembles. Une plage
désigne aussi ses éléments intermédiaires : « des articles 20-12 à 20-14 » crée
le 20-13. Peu de cas, mais le piège coûte cher : un article créé par le texte
n'existe pas dans le droit en vigueur, et le chercher conduit à le déclarer
introuvable.

## 6. `cas_consolidation.jsonl` — appliquer au bon endroit (10 cas)

```json
{"id": "S001", "source": "phrase ajoutée au dernier alinéa du I",
 "article": ["I. - Les dispositions …", "1° …", "2° …", "Un décret …", "II. - …"],
 "operations": [{"type": "ajouter_phrase", "designation": "Le dernier alinéa du I",
                 "nouveau": "Ce décret est pris après avis de l'Autorité de régulation."}],
 "attendu": {"apres_alinea": 3, "marque": "ajo", "texte": "Ce décret est pris …"}}
```

**Fonction : `consolider(article, operations) -> dict`**

Retourner :

```json
{"lignes": [[{"e": "", "t": "texte inchangé"},
             {"e": "ajo", "t": " phrase ajoutée"}],
            [{"e": "sup", "t": "alinéa supprimé"}]],
 "non_appliquees": [{"type": "…", "motif": "…"}]}
```

Une ligne est une liste de segments ; `e` vaut `""` (inchangé), `"sup"`
(supprimé) ou `"ajo"` (ajouté). Ce découpage est ce qui permet de rendre un
texte consolidé en suivi de modifications.

Ce que le banc vérifie, selon les clés du cas :

| clé de `attendu` | vérification |
|---|---|
| `refusee` | l'opération devait figurer dans `non_appliquees` |
| `aucun_barre` | aucun segment `sup` dans le consolidé |
| `barre` | ce texte est barré |
| `texte` | ce texte est ajouté |
| `position` | rang du segment ajouté parmi tous les segments |
| `apres_alinea` | le texte est **dans** la ligne de cet index, non dans une ligne à part |
| `ligne_touchee` | la marque attendue porte sur cette ligne précise |
| `contient` | le consolidé contient ce texte |
| `conserve` | le consolidé n'a pas perdu ce texte |

`apres_alinea` est le cas le plus discriminant : une phrase ajoutée à un alinéa
reste dans cet alinéa, elle ne devient pas un alinéa autonome.
