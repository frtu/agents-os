# Project - agents-os

## About
	
Operating System controlling agents for a specific tasks. Based on `User` input & registered `Tool`, `AgentOS` calls `LLM` to decide when to call `Memory` or `Agent` :

![Architecture](./_docs_/images/AgentOS.png)

## Modules

### Planning Module

#### Function Registry

Provides a store for all the function definitions and parameters. Used :

* when passing available tools / functions to LLM
* for matching completion response and calling Tools or Agents

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

#### Embedding (Short term memory) - TBD

Storage for raw knowledge

#### Fine tuning (Long term memory) - TBD

Storage for assimilated knowledge

### Action Module

Action module happen when an operation needs to be achieved (Maths, Retrieval, etc)

#### Agents - TBD

Customized agent with a specific Profile / Persona

#### Human - TBD

Interface to allow user to take action & respond. Human interaction should be time framed to avoid process to be blocked indefinitively.

## Appendix

### Release notes

#### 0.1.0-SNAPSHOT - Current version

* Static Function Registry

### See also

* [OpenAPI Chat completion API](https://platform.openai.com/docs/guides/text-generation/chat-completions-api)
* Originated from [jupyter-workbench/\_docs\_/llm](https://github.com/frtu/jupyter-workbench/tree/master/_docs_/llm)

