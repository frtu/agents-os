# Knowledge base

## Overview for Q&A

Instead of letting LLM use his general knowledge and adhoc phrase the answer, an enterprise can build their own **enterprise knowledge base** to allow LLM to use it correctly & not guess.

## Building a knowledge base

Building the knowledge base should be **predictable and tested** to ensure high level quality of the information (normally higher than letting LLM guess).

The process usually involves

* Entity extraction : retrieve all the entity / nodes
* Relationship & properties connection : connecting entity with KV attributes allowing more subteties when retrieving
