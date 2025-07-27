# Knowledge base

## Overview for Q&A

Instead of letting LLM use his general knowledge and adhoc phrase the answer, an enterprise can build their own **enterprise knowledge base** to allow LLM to use it correctly & not guess.

## Metadata / Tags

Request mgmt & Cataloging

Research metadata

### Intrinsic attributes of data

* volatility : low volatility (structural) vs high volatility (operational)
* structure vs unstructured

### Security

* private public
* Tagged / enriched by company

## Building a knowledge base

Building the knowledge base should be **predictable and tested** to ensure high level quality of the information (normally higher than letting LLM guess).

Building blocks :

* Nodes / Entities
* Relationship / Edge
* Properties

The process usually involves :

* Entity extraction : retrieve all the entity / nodes
* Relationship & properties connection : connecting entity with KV attributes allowing more subteties when retrieving


Based on volatility

* realtime vs batch

## Retrieval

Steps

* entity identification
* relationship navigation

Relevance instead of Resemblance 

### Processing - Aggregation

Pulling filter agg sort

### Security

Data access must be subjective : 

* who can see what?

The perfect test for security is two users with different profiles should see 2 different "projection" of the same data.


## See also

* https://stackoverflow.co/teams/resources/knowledge-base-101/
* [From Local to Global: A GraphRAG Approach to
Query-Focused Summarization](https://arxiv.org/pdf/2404.16130O)
* [GraphRAG](https://github.com/Graph-RAG/GraphRAG)