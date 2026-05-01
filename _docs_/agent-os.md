# Operating system for Agent

Agent OS : building blocks

## Foundation

### Interaction level

1. Interface with human (Flow) : smooth interaction allowing comprehension & non ambiguous collection of "what's needed"
2. Interface with machine (API) : specific & non ambiguous interaction with system

For design, let's bottom up (demand driven) :
- Machine interface should define specific template of all that is required
- Human interface / Flow is the step by step collection for it

#### Capabilities - Machine Interface

##### Slash comands

Shortcut

##### Tools

Generic function calls

##### Skills

Specialized reusable and composable

##### MCP

Integration with external

#### Workflow - Human Interface

Processes : for a specific persona & use case, define the decision tree to allow triggering Tasks (sequential or not) 

Tasks <=> Skills?
Composable

##### Security Permissions

Default to whitelist approach : ask more rather than less

Overrided by :

- Bypass permission
- Don't ask

### Session - Operating context

- Context windows
- Context rot

#### Bootstrap

Agent.md or Claude.md => ~200 lines
Index for others files

#### Context management

- Handling by machine : automatic capture of the session. Auto compaction (as efficient as possible)
- Handling by human : Based on human judgement

#### Plan mode

Prepare context before it gets overloaded with executions

### Memory across session

Hooks
