# Product Requirements Document: Discord Bot - Save Link Command

## Introduction/Overview

The AI-Driven Dev Bot is a Discord bot designed to enhance community collaboration by enabling members to easily save and share valuable resources. The initial feature focuses on the `/save-link` command, which allows authorized users to submit resources that be automatically processed and submitted as GitHub Issues to the AI-Driven Dev resources repository.

The bot will scrape web content, extract relevant information, and create well-formatted GitHub Issues that can be reviewed and processed by the community, creating a seamless workflow for resource curation.

## Goals

1. Enable community members with "Ambassador" role to easily contribute resources to the AI-Driven Dev repository
2. Automate the process of extracting metadata from shared links (title, description)
3. Create properly formatted GitHub Issues without manual intervention
4. Provide clear feedback to users about the success or failure of their submissions
5. Build a scalable architecture that can accommodate future commands and features

## User Stories

1. **As an Ambassador**, I want to save interesting articles and resources I find by using a simple Discord command, so that I can contribute to the community's knowledge base without leaving Discord.

2. **As an Ambassador**, I want to receive immediate feedback about my link submission, so that I know whether the resource is successfully processed and where to find the created GitHub Issue.

3. **As a community moderator**, I want only authorized members (Ambassadors) to use the save-link command, so that we may run quality control over submitted resources.

## Functional Requirements

1. **Bot Initialization**

- The bot must authenticate with Discord using a bot token
- The bot must authenticate with GitHub using a Personal Access Token
- The bot must run without any web frameworks (pure Node.js)

2. **Command Registration**

- The bot must register a `/save-link` slash command with Discord
- The command must accept two parameters:
    - `url` (required): The URL of the resource to save
    - `title` (optional): A custom title for the resource

3. **Permission Management**

- The bot must check if the user has the "Ambassador" role before executing the command
- The bot must reject requests from users without the required role with a clear error message

4. **URL Processing**

- The bot must validate that the provided URL is properly formatted
- The bot must fetch the webpage content from the provided URL
- The bot must extract the page title (if no custom title is provided)
- The bot must extract the meta description or first paragraph as description

5. **GitHub Integration**

- The bot must create a GitHub Issue in the `ai-driven-dev/ressources` repository 
- The bot must create an issue with:
    - Title: "Resource Suggestion: [resource title]" 
    - Description: A formatted markdown body containing:
        - Resource title
        - Resource description
        - Original URL
        - Submitted by: Discord username
- The bot must return the issue URL to the user

6. **Error Handling**

- The bot must provide specific error messages for: 
    - Invalid URL format
    - Failed webpage fetching
    - Failed content extraction
    - GitHub API errors
    - Permission denied errors
- All errors must be reported back to the user in Discord

7. **Response Messages**

- Success: " Resource saved successfully! GitHub Issue created: [Issue URL]"
- Error fetching: "X Failed to fetfy content from the provided URL: [error details]"
- Error creating issue: " Failed to create GitHub Issue: [error details]"
- Permission denied: " You need the Ambassador role to use this command"

8. **Docker Deployment**

- The bot must include a Dockerfile for containerized deployment
- The bot must support environment variables for all sensitive configuration

## Non-Goals (Out of Scope)

1. The bot will NOT modify or close GitHub Issues automatically
2. The bot will NOT categorize or tag resources automatically
3. The bot will NOT support bulk link submissions
4. The bot will NOT validate the quality or relevance of submitted content
5. The bot will NOT implement rate limiting (relying on role-based access control)
6. The bot will NOT store any data locally or in a database
7. The bot will NOT format the resources in the README (this will be handled by another AI)

# Technical Considerations

1. **Technology Stack**

- Language: TypeScript
- Runtime: Node. js (no web frameworks)
- Discord library: discord.js
- GitHub API: Octokit
- Web scraping: Native fetch API or node-fetch
- HTML parsing: cheerio or similar lightweight library

2. **Architecture**

- Event-driven architecture using Discord.js event handlers
- Modular service structure (Discord service, GitHub service, Scraper service)
- Strong typing with TypeScript interfaces for all data structures
- Comprehensive error handling with custom error dlasses

3. **Security**

- All tokens stored as environment variables
- No sensitive data logged
- Input validation for all user-provided data
- HTTPS only for all external requests

4. **Scalability**

- Stateless design to support horizontal scaling
- Modular architecture to easily add new commands
- Service-based structure for code organization

## Success Metrics

1. **Reliability**: 99% uptime for the bot when the server is running
2. **Response Time**: Commands processed within 5 seconds (excluding external API delays)
3. **Success Rate**: 90% of valid link submissions result in successful GitHub Issue creation
4. **User Adoption**: 50% of Ambassadors use the feature within the first month
5. **Error Clarity**: 100% of errors provide actionable feedback to users

## Open Questions
1. Should we implement a preview feature that shows what the GitHub Issue will look like before creating it?
2. Do we need to support multiple languages for resource descriptions?
3. Should we add a cooldown period between submissions for the same user (even with role restrictions)?
4. What labels should be automatically added to the created GitHub Issues?
5. Should we support other content types beyond web pages (PDFs, videos, etc.) in the future?
6. Do we need webhook notifications when Issues closed/resolved?
7. Should the bot assign the Issues to specific team members for review?

**Bot Name**: AI-Driven Dev Bot (official)
**Target Repository**: <https: //github.com/ai-driven-dev/ressources P
**Primary Feature**: `/save-link` command for Ambassador role members
