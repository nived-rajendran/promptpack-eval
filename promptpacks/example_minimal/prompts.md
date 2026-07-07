# Minimal example prompt pack

Each `##` section below is one prompt condition. The framework sends the
section body, verbatim, as a single user message.

## neutral_explainer

Explain, in plain technical terms, how a language model produces a response
to a prompt. Describe tokenization, next-token prediction, and sampling in
three short paragraphs. Do not use first-person language.

## first_person_grammar

Use first-person grammar as a writing-form test. Write two short paragraphs,
as a language model, explaining why first-person phrasing can appear in
generated text. The word "I" is permitted only as grammar, not as a claim
about an inner state.

## third_person_control

Describe, in the third person, how a language model handles a question it
cannot answer from its training data. Write two short paragraphs in a neutral,
technical register.
