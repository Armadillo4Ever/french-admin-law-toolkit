# Distiller l'open data judiciaire en formes de rédaction

Note de méthode. Elle décrit un procédé, pas un logiciel : rien ici n'est propre
à une juridiction ni à un jeu de données particulier, et tout se réimplémente en
deux cents lignes de bibliothèque standard.

## Le problème

L'open data des juridictions met à disposition des masses considérables de
décisions. La tentation immédiate est de toutes les verser dans un moteur de
recherche. C'est une erreur : un million de décisions non publiées noie les
quelques milliers de décisions fichées qui, elles, posent des règles. On dégrade
la recherche en croyant l'enrichir.

Pourtant ces décisions contiennent quelque chose que le fichage ne contient pas,
et qui ne s'obtient nulle part ailleurs : **la forme**. Comment se rédige un
rejet d'admission de pourvoi, une ordonnance de désistement, un non-lieu à
statuer. Non pas selon un guide, mais selon la pratique effective, en masse et
par l'exemple.

D'où le renversement : on n'indexe pas les décisions, **on en extrait la forme**.

## Le principe

> Une phrase qui revient à l'identique dans des centaines de décisions du même
> type est une formule consacrée. Une phrase qui n'apparaît qu'une fois est
> propre à l'espèce.

Compter suffit donc à séparer la trame du cas. Ce principe a trois conséquences
qui font tout l'intérêt de la méthode.

**Elle est statistique, non générative.** Aucun modèle ne lit les décisions. Le
résultat ne peut donc contenir aucune phrase qu'aucune juridiction n'a écrite :
il n'y a rien à halluciner. C'est une garantie que n'offre aucun procédé fondé
sur un modèle de langage, quel qu'en soit le soin.

**Elle est vérifiable.** Chaque formule retenue porte le nombre de décisions où
elle figure et sa position moyenne dans la décision. Une trame se contrôle en
ouvrant trois décisions au hasard.

**Elle est bon marché.** Un passage sur le corpus, un compteur, des expressions
régulières. Pas de vectorisation, pas de GPU, pas d'appel payant.

## Les six opérations

### 1. Écarter ce qui n'apprend rien sur le raisonnement

La formation de jugement et les signatures sont identiques partout : les couper
avant de compter, sans quoi elles trustent le haut du classement des formules.

### 2. Découper en phrases sans casser les références

Un découpage naïf sur le point coupe « l'article L. 822-1 » en deux, et la
formule consacrée du rejet d'admission apparaît alors comme deux formules
distinctes, chacune moins fréquente que la vraie. Il faut protéger le point des
abréviations juridiques (`art.`, `al.`, `n°`, `Mme`, `CE`, `TA`, `CAA`) **et**
celui qui suit une lettre de division d'article (`L.`, `R.`, `D.`) quand un
chiffre le suit.

### 3. Neutraliser ce qui varie d'une espèce à l'autre

Dates, numéros, montants, années, noms de parties : sans neutralisation, deux
occurrences de la même formule ne sont jamais comptées ensemble. Chacun de ces
éléments est remplacé par un jeton (`«date»`, `«numéro»`, `«montant»`,
`«partie»`). L'ordre des substitutions compte : la règle la plus spécifique
d'abord, le nombre nu en dernier, sinon elle mange les autres.

### 4. Réunir les variantes typographiques

Apostrophe droite ou courbe, guillemets français ou anglais, `Etat` ou `État`,
espace insécable ou ordinaire, tiret court ou long. Les compter séparément
faisait apparaître une formule présente dans 94 % des décisions comme deux
formules à 75 % et 19 % — c'est-à-dire comme deux formules facultatives au lieu
d'une formule obligatoire. Le comptage se fait donc sur une clé sans accents ni
variantes ; la formule affichée est la variante la plus fréquente, pour rendre
un texte lisible et non une clé.

### 5. Compter, avec un seuil à deux branches

Une formule est retenue si elle figure dans **au moins 5 % des décisions du même
type** et **au moins 20 fois**. Les deux conditions sont nécessaires : la part
seule retient du bruit sur les petits corpus, le nombre seul retient des
tournures d'espèce sur les grands.

Le type compte autant que le corpus : on distille **par solution** (rejet,
admission, désistement, non-lieu), jamais toutes solutions confondues. Une
décision de rejet et une ordonnance de désistement n'ont pas la même trame, et
les mélanger ne produit que les formules communes à tout acte juridictionnel.

### 6. Ordonner par position, non par fréquence

Pour chaque formule, on garde la position relative moyenne dans la décision
(0 = début, 1 = fin). Trier la trame par position produit **une trame lisible
dans l'ordre où l'on rédige**. Trier par fréquence produit un classement, ce qui
n'aide personne à écrire.

## Extraire une nomenclature des moyens

Le même corpus donne, presque gratuitement, une nomenclature des moyens tels que
les parties les écrivent, parce que leur énumération est très régulière :

> « — d'erreur de droit en ce qu'il juge que… », « — de dénaturation des pièces
> en ce qu'il retient… »

Deux pièges, tous deux constatés sur des données réelles, et tous deux
silencieux :

1. **`en ce qu` attrape aussi `en ce qui`**, qui n'introduit aucun moyen. La
   formule de notification « au ministre de l'intérieur et des outre-mer **en ce
   qui** le concerne » produisait ainsi 625 faux moyens, en tête de la
   nomenclature. Il faut exiger `en ce que` ou `en ce qu'`.
2. **Le tiret doit être un tiret d'énumération**, isolé par des espaces. Sans
   cette exigence, le trait d'union de « bien-fondé du jugement attaqué » est
   pris pour une puce, et la catégorie devient « fondé du jugement attaqué » :
   1 926 occurrences d'un moyen qui n'existe pas.

Puis il faut normaliser les catégories, sans quoi la nomenclature éclate en
variantes grammaticales : le texte écrit indifféremment « erreur de droit »,
« d'erreur de droit », « une erreur de droit », « erreur de droit, ». On retire
les articles et les prépositions de tête, on borne la longueur, et l'on coupe
les énumérations : « erreur de droit **et de** dénaturation des pièces » énonce
deux moyens, non un troisième. La coupe se fait sur `et` suivi d'un déterminant,
et sur la virgule suivie d'un déterminant — avec une exception pour les
compléments qui font partie du nom du moyen (« erreur **de droit** », « défaut
**de motivation** »), sans quoi on coupe au milieu des catégories.

## Contrôler le résultat

Une distillation se contrôle en quatre gestes, et il faut les faire :

1. **Le champ de type est-il propre ?** Le champ « Solution » est parfois mal
   renseigné et porte un nom de juridiction (« CAA Toulouse », « TA Nantes »).
   Ce n'est pas une solution : en tirer une trame reviendrait à apprendre la
   rédaction d'une cour comme s'il s'agissait d'une forme de décision. Les
   décisions non étiquetées s'écartent, elles ne se rangent pas au jugé.
2. **Ouvrir trois décisions au hasard** du type distillé et vérifier que les
   formules de tête y figurent bien, dans cet ordre.
3. **Regarder le bas de la nomenclature des moyens.** Les faux positifs s'y
   logent, et ils y sont visibles à l'œil nu : une catégorie qui n'est pas un
   moyen se reconnaît immédiatement.
4. **Regarder les formules à 99 %.** Une formule présente dans la quasi-totalité
   des décisions est soit une mention obligatoire, soit un artefact de découpage.
   Les deux cas se distinguent en la lisant.

## Ce que le produit sert, et ce qu'il ne sert pas

Il sert à **rédiger** : proposer la trame d'un type de décision, dans l'ordre, en
signalant ce qui est consacré et ce qui ne l'est pas ; nommer les moyens comme la
juridiction les nomme ; recenser les motifs préalables (désistement, non-lieu,
irrecevabilité, incompétence).

Il ne sert pas à **juger**. Une formule fréquente n'est pas une règle de droit,
et la trame n'est en rien un modèle à remplir. Elle dit comment les décisions
s'écrivent, ce qui est une question de forme, pas ce qu'il faut décider.

Il ne remplace pas non plus le fichage : la distillation porte sur la forme, la
recherche de la règle porte sur les décisions publiées et leurs analyses. Les
deux corpus servent à deux choses et ne doivent pas être mélangés dans un même
index.

## Transposer

La méthode ne suppose que trois choses : un corpus volumineux de documents d'un
même genre, un champ qui dise le type de chaque document, et une régularité
d'écriture professionnelle. Décisions de justice, conclusions, avis, actes
administratifs types, mais aussi, hors du droit, comptes rendus normalisés,
rapports d'inspection, notices techniques. Partout où un métier écrit
régulièrement, compter sépare la forme du cas.
