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

https://claude.com/plugins/skill-creator
https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md

https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

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

context /

- product : persona/audience, VoC, positioning
- tech : architecture, db, api, test
- workflows : change management

#### Context management

- Handling by machine : automatic capture of the session. Auto compaction (as efficient as possible)
- Handling by human : `/resume`. Based on human judgement

#### Plan mode

Prepare context before it gets overloaded with executions

### Memory across session

Hooks
