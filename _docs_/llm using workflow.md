# Needs for Durable Workflow

## Problem with AI

On Level 1, the user is directly exposed to LLM execution that may take multiple second in order to execution & returned to User.

On Level 2, execution time is multiplied by the number of call to LLM that may require to excute over a long period, handle error & retry.

On level 3, execution may involve complex interaction between machine & human. Human involvement require longer time to get an answer & execution has to pause until user responde and workflow can resume from previous state.

![Interaction mode](./images/Interaction mode.png)

## Solution

We will rely on [Temporal](https://temporal.io/) in order to pause & resume execution over a long period of time (see [durable workflow](https://github.com/frtu/lib-toolbox/blob/master/kotlin/workflows/durable_workflow.md)).
