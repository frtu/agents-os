## Technical guide

### Development with Claude Code

Before starting any project, you have to get familiar with your tools (see [Onboarding](#Onboarding) below)

#### By Project

Your project is built by **capturing spec** (context engineering) :

* [Claude Memory management](https://docs.anthropic.com/en/docs/claude-code/memory#determine-memory-type)

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