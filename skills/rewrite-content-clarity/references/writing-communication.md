# Writing Communication

**Origin:** Amazon writing culture ("Write Like an Amazonian")

Practical guidelines for clear, data-driven business communication. These techniques help engineers and managers write documents that drive decisions rather than delay them.

## Core Principles

| Principle          | Rule                            | Why It Matters                                    |
| ------------------ | ------------------------------- | ------------------------------------------------- |
| **Be Direct**      | < 30 words per sentence         | Short sentences aid comprehension and retention   |
| **Be Data-Driven** | Replace adjectives with metrics | Data enables decisions; adjectives invite debate  |
| **Be Objective**   | Eliminate weasel words          | Vague language hides gaps and slows resolution    |
| **Be Accessible**  | Avoid jargon; define acronyms   | Excludes non-experts; blocks cross-team alignment |

## Weasel Words

Weasel words sound meaningful but provide no actionable information. They hide missing data behind vague language.

### Weasel Word Patterns

| Pattern           | Examples                                    | Issue                                      |
| ----------------- | ------------------------------------------- | ------------------------------------------ |
| Vague quantifiers | "nearly all", "most", "many", "some"        | Replace with specific number or percentage |
| Hedge words       | "might", "may", "could", "should"           | State confidently or quantify uncertainty  |
| Vague modifiers   | "significantly", "substantially", "greatly" | Replace with metric                        |
| Attribution gaps  | "some experts say", "it's widely accepted"  | Cite source or remove                      |

### Common Offenders

| Weasel Phrase             | Problem                    | Data-Driven Alternative                |
| ------------------------- | -------------------------- | -------------------------------------- |
| "significant improvement" | Improved by how much?      | "25% reduction in latency"             |
| "nearly all customers"    | How many exactly?          | "87% of Prime members"                 |
| "low latency"             | How low? Compared to what? | "TP90 latency of 1ms (down from 10ms)" |
| "much faster"             | Faster by what measure?    | "reduced from 10ms to 1ms"             |
| "some experts suggest"    | Which experts?             | Cite the source or omit                |
| "it's widely accepted"    | Accepted by whom?          | State the authority or data            |

### Prohibited Phrases

Never use these in decision documents:

- "would help the solution"
- "might bring clarity"
- "should result in benefits"
- "significantly better"
- "arguably the best"

## Word Replacements

| Verbose                     | Direct    |
| --------------------------- | --------- |
| due to the fact that        | because   |
| in order to                 | to        |
| at this point in time       | now       |
| the majority of             | most      |
| in the event that           | if        |
| with regard to              | about     |
| prior to                    | before    |
| subsequent to               | after     |
| in spite of the fact that   | although  |
| for the purpose of          | to        |
| in the near future          | soon      |
| a large number of           | many      |
| on a daily basis            | daily     |
| at the present time         | now       |
| in the process of           | currently |
| has the ability to          | can       |
| is able to                  | can       |
| totally lack the ability to | could not |
| make a decision             | decide    |
| take into consideration     | consider  |
| give consideration to       | consider  |

## The So-What Test

Before sending any document, ask:

1. **Does the reader understand why I'm writing?**
2. **Does the reader know what action to take?**

If you can't answer both, rewrite until you can.

### Amazon Response Types

When answering questions, use one of four forms:

| Response                                     | When to Use                      |
| -------------------------------------------- | -------------------------------- |
| **Yes**                                      | Affirmative with confidence      |
| **No**                                       | Negative with confidence         |
| **A number**                                 | Quantifiable answer              |
| **"I don't know, will follow up by [date]"** | Unknown but committed to resolve |

## Before/After Examples

### Performance Communication

| Before (Weasel)                                    | After (Data-Driven)                                                                              |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| "We made the performance much faster"              | "We reduced server-side TP99 latency from 10ms to 1ms"                                           |
| "Customer complaints have increased significantly" | "Customer complaints increased by 25% in the past month, particularly regarding shipping delays" |
| "Sales increased significantly in Q4"              | "Unit sales increased by 40% in Q4 2011, compared to Q4 2010, because of holiday promotions"     |

### Product Description

| Before (Vague)                          | After (Specific)                                                                                                        |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| "The new product is innovative"         | "The new product features a sleek design and intuitive user interface that make it easy for customers to interact with" |
| "Our product is exceptional"            | "Our product has a customer satisfaction rate of 95%"                                                                   |
| "Our product might increase efficiency" | "Our product has been shown to increase efficiency by 20%"                                                              |

## Acronym Handling

Always define acronyms on first use:

> "After we sign the Non-Disclosure Agreement (NDA)..."

**Format:** `{Full Term} ({ACRONYM})`

## Document Formats

Consider alternative structures for different purposes:

| Format         | Best For                         | Key Characteristic                    |
| -------------- | -------------------------------- | ------------------------------------- |
| **1-pager**    | Quick decisions, status updates  | Single-page constraint forces clarity |
| **6-pager**    | Complex proposals, strategy docs | Narrative flow, no slides             |
| **Appendix**   | Supporting data, charts, tables  | Keeps main doc focused                |
| **RACI chart** | Roles and responsibilities       | Clear accountability                  |

## Adjectives Needing Data

Flag subjective adjectives that should have metrics:

| Adjective                  | Prompt                        |
| -------------------------- | ----------------------------- |
| fast, slow                 | How fast? Latency/throughput? |
| good, bad, excellent, poor | By what measure?              |
| large, small, big          | What quantity?                |
| significant, major, minor  | What percentage?              |
| better, worse              | Compared to what baseline?    |
| efficient, effective       | What metric proves this?      |

## Red Flags in Writing

- Adjectives without supporting metrics
- Sentences over 30 words
- Undefined acronyms
- Vague timeframes ("soon", "shortly")
- Missing "so what" or call to action
