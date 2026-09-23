# Distilling judicial open data into drafting forms

French sources are quoted in free translation; the French text prevails.

Method note. It describes a process, not a piece of software: nothing here is
specific to a court or to a particular dataset, and everything can be
reimplemented in two hundred lines of standard library.

## The problem

The open data of the courts makes considerable masses of decisions available.
The immediate temptation is to pour them all into a search engine. That is a
mistake: a million unpublished decisions drown the few thousand abstracted
(*fichées*) decisions which, for their part, lay down rules. Search is degraded
in the belief that it is being enriched.

Yet these decisions contain something that the abstracting does not contain,
and which is obtainable nowhere else: **the form**. How a refusal of leave to
appeal on points of law (*rejet d'admission de pourvoi*), a discontinuance
order, a decision of no need to adjudicate are drafted. Not according to a
guide, but according to actual practice, in bulk and by example.

Hence the reversal: the decisions are not indexed, **their form is extracted**.

## The principle

> A sentence that recurs identically in hundreds of decisions of the same type
> is an established formula. A sentence that appears only once is specific to
> the case.

Counting is therefore enough to separate the template from the case. This
principle has three consequences that make the whole interest of the method.

**It is statistical, not generative.** No model reads the decisions. The result
therefore cannot contain any sentence that no court has written: there is
nothing to hallucinate. That is a guarantee that no process based on a language
model offers, however careful.

**It is verifiable.** Each formula retained carries the number of decisions in
which it appears and its average position in the decision. A template can be
checked by opening three decisions at random.

**It is cheap.** One pass over the corpus, a counter, regular expressions. No
vectorisation, no GPU, no paid call.

## The six operations

### 1. Discard what teaches nothing about the reasoning

The composition of the bench and the signatures are identical everywhere: cut
them before counting, otherwise they monopolise the top of the ranking of
formulas.

### 2. Split into sentences without breaking references

A naive split on the full stop cuts "article L. 822-1" in two, and the
established formula of the refusal of leave to appeal then appears as two
distinct formulas, each less frequent than the real one. The full stop must be
protected in legal abbreviations (`art.`, `al.`, `n°`, `Mme`, `CE`, `TA`, `CAA`)
**and** after a letter marking the division of an article (`L.`, `R.`, `D.`)
when a digit follows it.

### 3. Neutralise what varies from one case to another

Dates, numbers, amounts, years, names of parties: without neutralisation, two
occurrences of the same formula are never counted together. Each of these
elements is replaced by a token (`«date»`, `«numéro»`, `«montant»`,
`«partie»`). The order of the substitutions matters: the most specific rule
first, the bare number last, otherwise it eats the others.

### 4. Merge typographic variants

Straight or curly apostrophe, French or English quotation marks, `Etat` or
`État`, non-breaking or ordinary space, short or long dash. Counting them
separately made a formula present in 94 % of decisions appear as two formulas
at 75 % and 19 %, that is, as two optional formulas instead of one mandatory
formula. Counting is therefore done on a key without accents or variants; the
formula displayed is the most frequent variant, so as to return readable text
and not a key.

### 5. Count, with a two-limb threshold

A formula is retained if it appears in **at least 5 % of decisions of the same
type** and **at least 20 times**. Both conditions are necessary: the share
alone retains noise on small corpora, the count alone retains case-specific
turns of phrase on large ones.

The type matters as much as the corpus: distillation is done **by outcome**
(dismissal, admission, discontinuance, no need to adjudicate), never with all
outcomes lumped together. A dismissal decision and a discontinuance order do not
have the same template, and mixing them produces only the formulas common to
every judicial act.

### 6. Order by position, not by frequency

For each formula, the average relative position in the decision is kept
(0 = beginning, 1 = end). Sorting the template by position produces **a template
readable in the order in which one drafts**. Sorting by frequency produces a
ranking, which helps nobody to write.

## Extracting a nomenclature of pleas

The same corpus yields, almost for free, a nomenclature of the pleas (*moyens*)
as the parties write them, because their enumeration is very regular:

> "- of error of law in that it holds that…", "- of distortion of the
> documents in that it finds…"

Two traps, both observed on real data, and both silent:

1. **`en ce qu` also catches `en ce qui`**, which introduces no plea. The
   notification formula "to the Minister of the Interior and Overseas Territories
   **en ce qui** le concerne" (insofar as he is concerned) thus produced 625 false
   pleas, at the top of the nomenclature. `en ce que` or `en ce qu'` must be
   required.
2. **The dash must be an enumeration dash**, isolated by spaces. Without this
   requirement, the hyphen of "bien-fondé du jugement attaqué" (merits of the
   judgment under appeal) is taken for a bullet, and the category becomes "fondé
   du jugement attaqué": 1 926 occurrences of a plea that does not exist.

Then the categories must be normalised, otherwise the nomenclature splinters
into grammatical variants: the text writes indifferently "erreur de droit",
"d'erreur de droit", "une erreur de droit", "erreur de droit,". Leading
articles and prepositions are removed, the length is bounded, and enumerations
are cut: "erreur de droit **et de** dénaturation des pièces" (error of law and
distortion of the documents) states two pleas, not a third. The cut is made on
`et` followed by a determiner, and on the comma followed by a determiner, with
an exception for the complements that form part of the name of the plea
("erreur **de droit**", "défaut **de motivation**"), otherwise the cut falls in
the middle of categories.

## Checking the result

A distillation is checked in four steps, and they must be carried out:

1. **Is the type field clean?** The "Solution" (outcome) field is sometimes
   badly filled in and carries the name of a court ("CAA Toulouse", "TA
   Nantes"). That is not an outcome: deriving a template from it would amount to
   learning the drafting of one court as if it were a form of decision.
   Unlabelled decisions are discarded; they are not sorted by guesswork.
2. **Open three decisions at random** of the distilled type and check that the
   leading formulas do appear there, in that order.
3. **Look at the bottom of the nomenclature of pleas.** The false positives
   lodge there, and they are visible to the naked eye: a category that is not a
   plea is recognised immediately.
4. **Look at the formulas at 99 %.** A formula present in almost all decisions
   is either a mandatory mention or a splitting artefact. The two cases are told
   apart by reading it.

## What the product serves, and what it does not serve

It serves to **draft**: propose the template of a type of decision, in order,
signalling what is established and what is not; name the pleas as the court
names them; list the preliminary grounds (discontinuance, no need to
adjudicate, inadmissibility, lack of jurisdiction).

It does not serve to **judge**. A frequent formula is not a rule of law, and the
template is in no way a model to be filled in. It says how decisions are
written, which is a question of form, not what must be decided.

Nor does it replace the abstracting: distillation bears on the form; the search
for the rule bears on the published decisions and their analyses. The two
corpora serve two purposes and must not be mixed in the same index.

## Transposing

The method assumes only three things: a large corpus of documents of the same
kind, a field that states the type of each document, and a regularity of
professional writing. Court decisions, submissions, opinions, standard
administrative acts, but also, outside the law, standardised reports,
inspection reports, technical notices. Wherever a profession writes regularly,
counting separates the form from the case.
