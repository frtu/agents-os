# Project - agents-os

## About

Operating System controlling agents for a specific tasks. Based on `User` input & registered `Tool`, `AgentOS`
calls `LLM` to decide when to call `Memory` or `Agent` :

![Architecture](./_docs_/images/AgentOS.png)

## Modules

### Planning Module

#### Function Registry

Provides a store for all the tool definitions and parameters. A tool can be a function or
an [action call to agent](#agents---tbd).

Can be used :

* when passing available tools to LLM
* for matching completion response and calling [Action module](#action-module)

##### Evolution

* [Currently] Static (configure locally with code)
* [Future] Ability to add function dynamically with API

#### Chat Completion

Calling LLM to define what function to call.

### Memory Module

#### Conversation

* system : System directive
* user : Interaction with User
* assistant : Agent / Assistant
* function : Function calls

```
with(Conversation()) {
    system("You are a helpful assistant.")

    chat.sendMessage(user("Who won the world series in 2020?"))
```

#### Intent recognition

Adding [IntentClassifierAgent.kt](service%2Fsrc%2Fmain%2Fkotlin%2Fcom%2Fgithub%2Ffrtu%2Fai%2Fos%2Fservice%2Fagent%2FIntentClassifierAgent.kt),
that test ability to provide Intent recognition / classification :

![Intent.png](_docs_%2Fimages%2FIntent.png)

#### Embedding (Short term memory) - TBD

Storage for raw knowledge

#### Fine-tuning (Long term memory) - TBD

Storage for assimilated knowledge

### Action Module

Action module happen when an operation needs to be achieved (Maths, Retrieval, etc)

#### Agents - TBD

Actions can be grouped into an Agent, which is a specialized entity / customized LLM with a specific Profile / Persona
(ex: `you are a 10 years specialized travel agent`).

This agent has can operate multiple actions / tasks
(ex: `your tasks is to propose a {{ num_of_days}} schedule to {{ destination }}`).

#### Human - TBD

Interface to allow user to take action & respond. Human interaction should be time framed to avoid process to be blocked
indefinitively.

## Appendix

### Release notes

#### 0.1.0-SNAPSHOT - Current version

* Static Function Registry

### See also

* [OpenAPI Chat completion API](https://platform.openai.com/docs/guides/text-generation/chat-completions-api)
* Originated from [jupyter-workbench/\_docs\_/llm](https://github.com/frtu/jupyter-workbench/tree/master/_docs_/llm)

