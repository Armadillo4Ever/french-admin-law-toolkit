# Banc Lebon : retrouver une décision ancienne avec une question d'aujourd'hui

## Ce que le banc mesure

Le Recueil Lebon de 1840 à 1960, numérisé par la BnF sur Gallica, contient les décisions qui ont fondé le
droit administratif. Un juriste d'aujourd'hui les cherche avec ses mots : « tribunal administratif »,
« recours pour excès de pouvoir », « permis de construire ». Le recueil emploie ceux de son temps :
« conseil de préfecture », « pourvoi », « permis de bâtir ». Le banc mesure si une recherche franchit
cet écart.

## Comment il est construit

Même principe que le [banc de fichage](../fichage/) : on retourne une annotation qui existe déjà. Le
fichage d'une décision au recueil (son sommaire et sa rubrique de classement) a été rédigé par un
arrêtiste ; c'est la réponse. On le fait réécrire, par un modèle de langage, en une question qu'un
juriste poserait aujourd'hui : vocabulaire contemporain, sans nom de partie, sans date, sans numéro.

- 99 décisions, neuf par décennie de 1850 à 1959, tirées au sort parmi celles dont le fichage est
  lisible (150 à 900 caractères, au moins 75 % de lettres : l'OCR ancien est souvent illisible) ;
- la cible est la décision elle-même, cherchée parmi toutes les décisions du fonds (67 636 dans notre
  essai).

Chaque ligne de [`banc_lebon.jsonl`](banc_lebon.jsonl) donne la question, la référence au recueil,
l'année et le lien vers le volume sur Gallica, où se lisent le fichage et le texte de la décision.

## Ses limites, à connaître avant de s'en servir

- **La réécriture est imparfaite.** Le modèle a gardé çà et là un terme ancien (« patente », « conseil de
  préfecture ») ; ces questions sont plus faciles qu'une vraie question contemporaine.
- **Le banc favorise le fichage.** Les questions étant tirées du fichage, une recherche qui le privilégie
  part avec un avantage ; et un procédé qui ajoute du vocabulaire ancien ne peut guère montrer ici son
  apport, puisque la question en contient déjà.
- **Les fichages lus par OCR sont bruités** : on y trouve des fins de motifs, des coquilles, des numéros
  de page. C'est la réalité du fonds, on ne l'a pas corrigée.

Comme pour les autres bancs, les chiffres comparent deux configurations sur le même banc ; ils ne
mesurent pas une qualité absolue.

## Ce qu'il nous a appris

Sur notre moteur (vecteurs bge-m3), en cherchant la cible parmi les 67 636 décisions :

| réglage | MRR | cible au rang 1 | dans les 5 premiers | dans les 20 premiers |
|---|---|---|---|---|
| texte lu par OCR seul (rubrique, fichage et texte mêlés) | 0,533 | 46 | 60 | 71 |
| fichage 0,7 + texte 0,3 | 0,663 | 58 | 76 | 84 |
| fichage 0,6 + texte 0,35 + plan de classement moderne 0,05 | 0,637 | 57 | 71 | 82 |
| fichage 0,5 + texte 0,3 + plan de classement moderne 0,2 | 0,457 | 39 | 52 | 64 |
| réglage retenu : fichage 0,7 + texte 0,3, vocabulaire ancien 0,3, décisions sans fichage classées sur leur texte | 0,639 | 57 | 72 | 82 |

Trois enseignements.

1. **Le fichage d'abord.** Chercher dans le fichage plutôt que dans le texte océrisé fait gagner douze
   cibles au premier rang. Le fichage est court, rédigé par un professionnel, dans le vocabulaire de
   classement ; le texte est long et bruité.
2. **Le rapprochement avec le plan de classement moderne nuit au classement**, même à faible dose : il
   donne le même score à toute une rubrique et noie la bonne décision parmi ses voisines. Il reste utile
   à l'affichage, pour situer la décision ; pas dans le score.
3. **Une décision sans fichage utile** (environ une sur quatre dans le fonds) doit être classée sur son
   texte, et non sur un vecteur de fichage vide ou réduit à la rubrique. Le banc, dont toutes les cibles
   ont un fichage, y perd un peu ; mais ces décisions redeviennent trouvables, et ce sont parfois des
   décisions de principe (sur l'imprévision ou les processions, dans notre essai).

## Le seuil d'affichage

Un moteur qui mêle décisions récentes et anciennes doit décider quand montrer un extrait du Lebon. Nous
avons comparé le meilleur score Lebon pour les 99 questions du banc et pour 60 questions modernes
(tirées du banc de fichage, décisions postérieures à 1990) :

| seuil | cibles Lebon affichées | questions modernes affichant un Lebon |
|---|---|---|
| 0,66 | 68 / 99 | 21 / 60 |
| 0,68 | 57 / 99 | 11 / 60 |
| 0,70 | 46 / 99 | 3 / 60 |
| 0,72 | 36 / 99 | 0 / 60 |

Nous avons retenu 0,70. Une question moderne qui fait remonter un Lebon n'est d'ailleurs pas toujours une
erreur : la décision ancienne peut être la décision de principe.

## Voir aussi

[`../../recherche/vocabulaire_lebon/`](../../recherche/vocabulaire_lebon/) : le répertoire des
correspondances entre vocabulaire contemporain et vocabulaire ancien.
