# Abstracting benchmark: measuring a legal search without annotating a single question

## The idea

The abstracting (*fichage*) of case law is an evaluation resource that nobody
uses as such. Each analysis pairs **a point of law written by a judge** with
**the decision that laid it down**. That is exactly a question and answer pair,
produced by an expert, on the substance of the law. There are tens of thousands
of them, and they are public.

A benchmark is expensive because it requires annotation: asking questions, then
judging, for each one, which sources are relevant. Here, the judgment already
exists. It only needs to be turned around: the statement of the point of law is
given to the engine, and we watch whether it retrieves the decision.

```
python3 construire_banc.py --analyses analyses.jsonl --decisions decisions_ids.jsonl -n 300
python3 ../mesurer.py --banc banc_fichage.jsonl --adaptateur mon_moteur.py --sortie avant.json
python3 ../mesurer.py --comparer avant.json apres.json
```

Standard library only. No model, no service, no network: the benchmark is built
offline, from your files. The format of the inputs is described in
[FORMAT.en.md](FORMAT.en.md).

To see the pipeline run without preparing anything, two example files
illustrate the expected format:

```
python3 construire_banc.py --analyses exemple_analyses.jsonl \
    --decisions exemple_decisions.jsonl -n 5 --sortie essai.jsonl
```

## What the benchmark measures, and what it does not measure

It measures **"I am looking for THE right answer"** search: starting from the
statement of a rule, does the engine retrieve the decision that laid it down?

It does **not** measure search by analogy, which is the other half of the job:
when the question is new, one reasons on a cluster of supporting authorities none
of which answers exactly, and the measure that matters is then recall on a
hand-judged cluster. That benchmark does not build itself.

Nor does it measure the quality of the drafting produced from the sources found.

## The three precautions that make the benchmark valid

**1. No leakage.** Since the question is drawn from an analysis, querying the
corpus of analyses would retrieve it verbatim, and the measure would be void.
Each question therefore carries `"cible": "decisions"`: only the full text of the
decisions may be queried. This is the easiest precaution to forget and the only
one that invalidates everything.

**2. No unfindable question.** A decision absent from the corpus queried cannot
be retrieved: keeping it would measure the coverage of the corpus, not the
quality of the search. Hence the second input file, which restricts the sampling
to the decisions actually available in full text.

**3. No classification path.** The first block of an abstract (*abrégé*) is a
heading of the classification scheme, written in capitals. Taking it for a
question would amount to measuring a match of nomenclature. It is discarded,
which also discards the older abstracts that consist of nothing else: the
benchmark therefore leans towards recent decisions. This is an accepted bias,
preferable to meaningless questions.

## The sampling

Without precaution, random sampling produces a benchmark massively composed of
recent decisions from the best-stocked publication level. The sampling is
therefore **stratified by classification level and by decade**, and
**reproducible**: same seed, same benchmark, from one run to the next and from
one machine to another. That is what makes it possible to compare two
configurations of an engine without the benchmark shifting underfoot.

The program displays the distribution obtained. Look at it: it tells you what
your overall figure really measures.

## Reading the figures

`../mesurer.py` returns, for each question and on average:

| measure | what it says |
|---|---|
| share of questions where at least one expected result is found | the outright failure rate |
| nDCG@10 | is the expected result **high** in the list, or drowned at rank 40? |
| recall@50 | what share of the expected results is retrieved, at a given depth |
| MRR | the reciprocal of the rank of the first expected result, averaged |
| median rank of the first expected result | the figure felt by the person searching |

The report also details, by corpus, which expected results were returned and at
what rank **within that corpus**: in a multi-corpus search, the order between
corpora is a display convention, and the rank inside a corpus is what the eye
sees.

**What these figures are worth.** The relevance judgments are incomplete by
construction: an excellent decision that the analysis does not cite counts here
as irrelevant and unfairly penalises the engine. These figures serve to
**compare two configurations on the same benchmark, with the same `k`**. They do
not measure an absolute quality, and two different benchmarks cannot be
compared.

## Transposing

Nothing in the method is specific to the administrative courts. All that is
needed is a corpus where someone has already written, next to each document, what
that document contributes: the summaries (*sommaires*) of the Court of Cassation
(*Cour de cassation*), the case-law summaries of the Court of Justice, the case
notes of the European Court of Human Rights, but also, outside the law, any
document corpus indexed by professionals. The question to ask is always the
same: **does the annotation already exist, in another form, in the data?**
