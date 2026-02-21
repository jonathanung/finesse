---
description: "Fetch a Linear issue and plan it with /finesse or /finesse-mini"
argument-hint: "LINEAR_ISSUE [--max-refinements N] [--mini]"
allowed-tools: ["Skill", "AskUserQuestion"]
hide-from-slash-command-tool: "true"
---

# Finesse Linear — Issue-Driven Planning

Fetch a Linear issue via MCP and delegate to `/finesse` or `/finesse-mini` with a structured task description. This is a lightweight wrapper — all planning logic lives in the delegated command.

## Argument Parsing

Parse `$ARGUMENTS`:

1. **Extract flags first:**
   - `--max-refinements N` — store N, remove from arguments. Passed through to `/finesse`.
   - `--mini` — store as boolean, remove from arguments. Delegates to `/finesse-mini` instead of `/finesse`.

2. **Extract issue identifier** from remaining arguments:
   - If the argument is a URL containing `issue/([A-Z]+-[0-9]+)`, extract the issue ID from the match.
   - If the argument matches `[A-Z]+-[0-9]+` directly, use it as the issue ID.
   - If neither pattern matches, say: "Could not parse a Linear issue ID. Provide a URL (e.g., `https://linear.app/team/issue/PF-254/...`) or a raw ID (e.g., `PF-254`)." and STOP.

3. **If `$ARGUMENTS` is empty or blank:** Ask the user for the Linear issue URL or ID using `AskUserQuestion`. Then parse the response as in step 2.

4. **If multiple issue-like arguments are present:** Use the first one. Say: "Multiple issues detected — using [ID]. Run `/finesse-linear` separately for each issue."

## Step 1: Fetch Issue Data

Call the MCP tool `mcp__linear-server__get_issue` with the extracted issue ID.

### If the MCP tool is unavailable

If the tool call fails because the MCP server is not configured or the tool is not found, display:

---

**Linear MCP Server Not Available**

`/finesse-linear` requires the Linear MCP server. To set it up:

1. Get a Linear API key from https://linear.app/settings/api

2. Add to your MCP configuration (`.mcp.json` in project root or `~/.claude/mcp.json` globally):

```json
{
  "mcpServers": {
    "linear-server": {
      "command": "npx",
      "args": ["-y", "@anthropic/linear-mcp-server"],
      "env": {
        "LINEAR_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

3. Restart Claude Code to load the server.

The server must be named `linear-server` so the tool `mcp__linear-server__get_issue` is available.

---

Then STOP. Do not proceed without issue data.

### If the issue is not found

Say: "Linear issue [ID] not found. Check the issue ID and try again." Then STOP.

### If there is a network or rate-limit error

Show the error and say: "Try again in a moment." Then STOP.

## Step 2: Format Issue Data

Build a structured task description from ALL available fields in the response. Use this format:

```
## Linear Issue: [ID] — [TITLE]

**Status:** [state name]
**Priority:** [priority level]
**Assignee(s):** [names, or "Unassigned"]
**Labels:** [names comma-separated, or "None"]
**Project:** [name, or "None"]
**Cycle:** [name, or "None"]
**Due date:** [date, or "None"]
**Estimate:** [points/value, or "None"]
**Git branch:** [branch name, or "None"]
**URL:** [issue URL]

### Description

[Full description text, or "No description provided."]
```

Then append these sections ONLY if data exists (omit entirely if empty):

**Parent Issue** — `[PARENT_ID] — [PARENT_TITLE] ([STATUS])`

**Sub-Issues** — Bulleted list: `- [SUB_ID] — [SUB_TITLE] ([STATUS])`

**Relations** — Bulleted list: `- [TYPE]: [RELATED_ID] — [RELATED_TITLE]`

**Comments** (chronological) — Each as: `**[AUTHOR]** ([DATE]): [TEXT]` separated by blank lines.

### Minimal issue handling

If the issue has a title but no description and no comments, append:

> Note: This Linear issue has minimal detail. The planning workflow will ask clarifying questions during the discovery phase.

## Step 3: Delegate

Invoke the appropriate Finesse command using the Skill tool:

**If `--mini` is set:**

Use Skill tool: `skill: "finesse-mini"`, `args: "<formatted task description>"`

**Otherwise:**

Use Skill tool: `skill: "finesse"`, `args: "<formatted task description> [--max-refinements N if specified]"`

The formatted task description becomes the `$ARGUMENTS` of the target command. The identity hook will intercept the delegated Skill invocation and inject planner identity rules as usual.

After invoking the Skill tool, this command's job is done. All subsequent interaction is handled by the delegated command.
