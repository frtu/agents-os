## Technical guide

### Development with Claude Code

Before starting any project, you have to get familiar with your tools (see [Onboarding](#Onboarding) below)

#### Interaction mode

##### Step by step

First ask AI for how to implement your feature using `Plan mode` :

* Trigger analysis & reflexion first

#### By Project

##### Local Memory

Your project is built by **capturing spec** (context engineering).

###### What

* Theory with [Cline Memory Bank](https://docs.cline.bot/prompting/cline-memory-bank)
* Examples with [Memory bank of AIDD](https://github.com/ai-driven-dev/rules/tree/main/memory-bank)

###### How

* [Claude Memory management](https://docs.anthropic.com/en/docs/claude-code/memory#determine-memory-type) using CLAUDE.md (potentially segregated by sub folders)
* Import from other files using `@`

Lifecycle

* Create your intial `CLAUDE.md` using slash command `/init`
* Use `#` to append
* Use slash command `/memory` to discuss with it

##### MCP

Using [existing available MCP](https://docs.anthropic.com/en/docs/claude-code/mcp) with `claude mcp add  -s project XXX`

*ATTENTION use carefully scoped -s (local/project/user) `claude mcp add -s project XXX`*

Other commands :

* `claude mcp list` : List all local MCP installed for the project
* `claude mcp add-from-claude-desktop ` : Import directly [from Claude Desktop](https://docs.anthropic.com/en/docs/claude-code/mcp#import-mcp-servers-from-claude-desktop)

##### Parallelism

* Work with 3 sub agents in parallel with an **Orchestrator** (Opus) and **Worker** (Sonnet)
* Work on 3 features in parallel using [git worktree](https://git-scm.com/docs/git-worktree)

Agent wrapper using

* https://github.com/ruvnet/claude-flow

##### Hooks

* Great examples with [notification, prevent rm, etc](https://github.com/disler/claude-code-hooks-mastery/blob/main/.claude/settings.json)

#### Onboarding

##### Flow

Using **Claude code in terminal** is like using Git with terminal, though UI can help on more specific actions, terminal is core.

* `claude -p <prompt>` : start a new task using prompt
* `claude -c` : continue by resuming from latest actions
* `claude -r` : resume from specific history

##### Commands

[Out of the box commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands) or [Recap](https://github.com/hesreallyhim/awesome-claude-code?tab=readme-ov-file#slash-commands-)

* `/` list all available commands
* `/project:` list project specific commands
* `/user:` list user specific commands

###### Custom commands

* Create your [custom commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands#custom-slash-commands) using [`@` for ext file inclusion](https://docs.anthropic.com/en/docs/claude-code/slash-commands#file-references)
* `$ARGUMENT` pass slash command argument into internal function

###### Knowledge base for custom commands

Knowledge base with [AIDD](https://github.com/ai-driven-dev/rules/tree/main/.cursor/rules)

See also

* https://medium.com/the-tech-collective/power-up-with-ai-the-developers-advantage-6a4a8f8d1b17	
* https://medium.com/@binoy_93931/from-agile-to-adaptive-intent-driven-development-aidd-the-ai-first-paradigm-shift-e07e5c7df1ec
* https://aiddbot.com/workflows-with-ai-dd
* https://www.pulsemcp.com/servers/skydeckai-aidd

##### Mode selection

Use `Shift + Tab` to switch between

* `Plan`
* `Act` & auto edit

##### Model selection

For **cost effectiveness** & generation **speed**, 

* use `sonnet` instead of `opus` if you were able to create a plan before coding.

##### Installation & Setup

[Installation](https://docs.anthropic.com/en/docs/claude-code/setup#native-binary-installation-beta)

```
curl -fsSL https://claude.ai/install.sh | bash
<OR>
npm install -g @anthropic-ai/claude-code
```

[Customize your terminal](https://docs.anthropic.com/en/docs/claude-code/terminal-config)

* Terminal bell notifications with ```claude config set --global preferredNotifChannel terminal_bell```
* Check version with claude cmd `/version`


[Configuration](https://docs.anthropic.com/en/docs/claude-code/settings#settings-files)

* `.claude/settings.json` : project settings (to commit)
* `.claude/settings.local.json` : project **personal** settings (NOT committed)
* `~/.claude/settings.json` : user **global** settings / instructions
* Configure [permissions](https://docs.anthropic.com/en/docs/claude-code/settings#permission-settings) (to avoid repetitive approval asks)
* Configure system [env](https://docs.anthropic.com/en/docs/claude-code/settings#settings-files) like ([async exec using `ENABLE_BACKGROUND_TASKS`](https://www.reddit.com/r/ClaudeAI/comments/1lkfz1h/how_i_use_claude_code/))


[Enabling Claude in IDE](https://docs.anthropic.com/en/docs/claude-code/ide-integrations#installation)

* Terminal : Run claude cmd `/ide`

##### VS Code

* Open a new Claude tab using `Cmd + Esc`
* When selecting a code in the left bar, you can see `Claude` tab highlight the context you can run command on (select specific lines OR whole file)


##### [Roo Code](https://github.com/RooCodeInc/Roo-Code)

Reuse Claude Code as an AI provider :

* Select provider using Roo Code > Settings > Providers > `API Provider` = `Claude Code`

##### CICD : Auto code review

Integrate with GitHub Action for [code review](https://github.com/marketplace/actions/ai-code-review-action)