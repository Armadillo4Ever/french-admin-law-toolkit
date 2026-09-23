# Legislative drafting benchmark

French sources are quoted in free translation; the French text prevails.

89 cases to measure whether a program, or a model, correctly reads the
instructions by which one French normative text amends another, and applies
them at the right place in the text in force.

```
python3 executer.py --adaptateur adaptateur_gabarit.py
python3 executer.py --adaptateur mon_adaptateur.py -v --famille lecture
python3 executer.py --adaptateur mon_adaptateur.py --json rapport.json
```

Standard library only, Python 3.8 or later. The benchmark embeds no
implementation: it calls yours through an adapter, a simple Python module in
which you fill in the functions that interest you. Copy
`adaptateur_gabarit.py`, fill it in, run. A missing function makes its family
"not covered": it counts neither as a pass nor as a failure, so you can handle
only one of them.

The exact contract of the inputs and outputs is in [FORMAT.en.md](FORMAT.en.md).

## The six families

| file | cases | question asked |
|---|---:|---|
| `cas_lecture.jsonl` | 25 | what operation does the instruction order, on what, with what? |
| `cas_traduction.jsonl` | 26 | the same, reduced to a single operation name |
| `cas_designation.jsonl` | 19 | where does "the third paragraph of 2° of I" fall in this article? |
| `cas_decompte.jsonl` | 6 | which lines make up the paragraph (*alinéa*) of rank *n*? |
| `cas_articles_crees.jsonl` | 3 | which articles does the text create, ranges included? |
| `cas_consolidation.jsonl` | 10 | is the operation applied at the right place in the text in force? |

## What the benchmark tries to catch out

The cases are not a random sample: each was added because an implementation, or
a model, had got it wrong. The pitfalls they cover:

1. **The operation is read from the verb, never from the set phrase.** "Ainsi
   rédigé" (worded as follows) is not an operator: the same phrase serves for
   replacement ("the first paragraph is worded as follows") and for insertion
   ("an article 12-1 worded as follows is inserted"). Taking the phrase for a
   sign of replacement turns an insertion into an overwrite, and the
   consolidated text loses provisions without anything signalling it.
2. **The target and the object are two different things.** "Chapter II is
   supplemented by an article 9-1" has a division as its target and an article
   as its object. Confusing them inserts at the wrong level.
3. **The instruction carries its own number.** In a draft text, an instruction
   begins with its label, not with its verb: "6° After article…", "a) After
   article…". A reading rule anchored at the start of the string does not see
   them.
4. **The auxiliary is elided in an enumeration.** Under "Article X is amended as
   follows:", the items take up the auxiliary by ellipsis: "2° The second
   paragraph replaced by…". Requiring "est" or "sont" (is or are) misses all
   these instructions.
5. **A table constitutes a single paragraph**, whatever the number of its rows.
   Counting a table row as a paragraph shifts all the following ranks, silently.
6. **A level runs to the next marker of the same level.** The unmarked
   paragraphs that follow a `2°` belong to it: the `2°` may have two paragraphs.
7. **A range designates its intermediate elements.** "Articles 20-12 to 20-14"
   also covers 20-13.
8. **The occurrence counts.** "The second occurrence of the words" is not the
   first.
9. **A sentence added to a paragraph stays in that paragraph**: it does not
   become a separate paragraph.
10. **An announcement of amendment is not an amendment.** "Article 12 is amended
    as follows:" introduces the operations without being one; rendering it as
    some type or other produces an empty operation, but a silent one.

## On the counting of paragraphs

The rule applied is that of the circular of 20 October 2000 on the method of
counting paragraphs (NOR PRMX0004462C), which aligned government practice with
parliamentary usage: **every line break opens a paragraph**, including the items
of an enumeration. It also applies to texts prior to 2000. The cases marked
`ancien` serve only to check that an implementation offering both counts does
not confuse them.

## Sources

The cases come from two places, indicated by the `source` field:

- the **Legislative Drafting Guide** (*Guide de légistique*, 4<sup>th</sup>
  edition, 2026), published by the General Secretariat of the Government and the
  Council of State (*Conseil d'État*), whose examples have been taken up or
  adapted;
- **observations made on real texts** during the summer of 2026: draft decrees
  and bills, codes in force. The cases have been rewritten so that they can no
  longer be linked to a particular file, but the grammatical form that had made
  the reading fail is kept as it was.

No case contains personal data or any non-public element.

## Contributing a case

A useful case is a case that made something fail. Add a line to the file of the
family concerned, with a free `id` and a `source` that says where the
requirement comes from, and declare in `attendu` only the fields you hold to be
enforceable: everything you put there becomes a constraint for all
implementations.
