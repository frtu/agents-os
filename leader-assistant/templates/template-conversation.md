---
Category: session
Id: {{conversation-id}}
Created: {{created}}
Tags: [{{tag-list}}]
Sdk-session-id: {{sdk-session-id}}
Pending-plan: {{plan}}
Pending-interaction: {{interaction}}
Template-type: mustache
---

# Conversation — {{conversation-name}}

{{#event-message}}
## {{role}} - {{event-time}}
{{message}}
{{/event-message}}