# Banc de légistique

89 cas pour mesurer si un programme, ou un modèle, lit correctement les
instructions par lesquelles un texte normatif français en modifie un autre, et
les applique au bon endroit du texte en vigueur.

```
python3 executer.py --adaptateur adaptateur_gabarit.py
python3 executer.py --adaptateur mon_adaptateur.py -v --famille lecture
python3 executer.py --adaptateur mon_adaptateur.py --json rapport.json
```

Bibliothèque standard uniquement, Python 3.8 ou plus récent. Le banc n'embarque
aucune implémentation : il appelle la vôtre à travers un adaptateur, un simple
module Python dont vous remplissez les fonctions qui vous intéressent. Copiez
`adaptateur_gabarit.py`, remplissez, exécutez. Une fonction absente rend sa
famille « non couverte » : elle ne compte ni en réussite ni en échec, et vous
pouvez donc n'en traiter qu'une.

Le contrat exact des entrées et des sorties est dans [FORMAT.md](FORMAT.md).

## Les six familles

| fichier | cas | question posée |
|---|---:|---|
| `cas_lecture.jsonl` | 25 | quelle opération l'instruction ordonne-t-elle, sur quoi, avec quoi ? |
| `cas_traduction.jsonl` | 26 | la même, ramenée à un nom d'opération unique |
| `cas_designation.jsonl` | 19 | où « le troisième alinéa du 2° du I » tombe-t-il dans cet article ? |
| `cas_decompte.jsonl` | 6 | quelles lignes composent l'alinéa de rang *n* ? |
| `cas_articles_crees.jsonl` | 3 | quels articles le texte institue-t-il, plages comprises ? |
| `cas_consolidation.jsonl` | 10 | l'opération est-elle appliquée au bon endroit du texte en vigueur ? |

## Ce que le banc cherche à prendre en défaut

Les cas ne sont pas un échantillon aléatoire : chacun a été ajouté parce qu'une
implémentation, ou un modèle, s'y était trompé. Les pièges qu'ils couvrent :

1. **L'opération se lit au verbe, jamais à la locution.** « Ainsi rédigé » n'est
   pas un opérateur : la même locution sert au remplacement (« le premier alinéa
   est ainsi rédigé ») et à l'insertion (« il est inséré un article 12-1 ainsi
   rédigé »). Prendre la locution pour un signe de remplacement transforme une
   insertion en écrasement, et le texte consolidé perd des dispositions sans que
   rien ne le signale.
2. **La cible et l'objet sont deux choses.** « Le chapitre II est complété par un
   article 9-1 » a pour cible une division et pour objet un article. Les
   confondre insère au mauvais niveau.
3. **L'instruction porte son propre numéro.** Dans un projet de texte, une
   instruction commence par son étiquette, non par son verbe : « 6° Après
   l'article… », « a) Après l'article… ». Une règle de lecture ancrée en tête de
   chaîne ne les voit pas.
4. **L'auxiliaire est élidé dans une énumération.** Sous « L'article X est ainsi
   modifié : », les items reprennent l'auxiliaire par ellipse : « 2° Le deuxième
   alinéa remplacé par… ». Exiger « est » ou « sont » fait manquer toutes ces
   instructions.
5. **Un tableau constitue un seul alinéa**, quel que soit le nombre de ses
   lignes. Compter une ligne de tableau pour un alinéa décale tous les rangs
   suivants, en silence.
6. **Un degré court jusqu'au marqueur suivant de même niveau.** Les alinéas non
   marqués qui suivent un `2°` lui appartiennent : le `2°` peut avoir deux
   alinéas.
7. **Une plage désigne ses éléments intermédiaires.** « Des articles 20-12 à
   20-14 » vise aussi le 20-13.
8. **L'occurrence compte.** « La deuxième occurrence des mots » n'est pas la
   première.
9. **Une phrase ajoutée à un alinéa reste dans cet alinéa** : elle ne devient pas
   un alinéa autonome.
10. **Une annonce de modification n'est pas une modification.** « L'article 12
    est ainsi modifié : » introduit les opérations sans en être une ; la rendre
    par un type quelconque produit une opération vide, mais silencieuse.

## Sur le décompte des alinéas

La règle appliquée est celle de la circulaire du 20 octobre 2000 relative au
mode de décompte des alinéas (NOR PRMX0004462C), qui a aligné la pratique
gouvernementale sur l'usage parlementaire : **tout retour à la ligne ouvre un
alinéa**, y compris les items d'une énumération. Elle s'applique aussi aux
textes antérieurs à 2000. Les cas marqués `ancien` servent seulement à vérifier
qu'une implémentation offrant les deux décomptes ne les confond pas.

## Sources

Les cas viennent de deux endroits, indiqués par le champ `source` :

- le **guide de légistique** (4<sup>e</sup> édition, 2026), publié par le
  secrétariat général du Gouvernement et le Conseil d'État, dont les exemples
  ont été repris ou adaptés ;
- des **observations relevées sur des textes réels** au cours de l'été 2026 :
  projets de décret et de loi, codes en vigueur. Les cas ont été réécrits pour
  n'être plus rattachables à un dossier particulier, mais la forme
  grammaticale qui avait fait échouer la lecture est conservée telle quelle.

Aucun cas ne contient de donnée personnelle ni d'élément non public.

## Contribuer un cas

Un cas utile est un cas qui a fait échouer quelque chose. Ajoutez une ligne au
fichier de la famille concernée, avec un `id` libre et une `source` qui dise
d'où vient l'exigence, et n'annoncez dans `attendu` que les champs que vous
tenez pour exigibles : tout ce que vous y mettez devient une contrainte pour
toutes les implémentations.
