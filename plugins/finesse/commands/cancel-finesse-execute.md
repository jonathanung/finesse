---
description: "Cancel an active Finesse execution loop"
allowed-tools: ["Bash(test -f .finesse/loop-state.md:*)", "Bash(rm .finesse/loop-state.md)", "Read(.finesse/loop-state.md)", "Read(.finesse/run-log.json)", "Write(.finesse/run-log.json)"]
hide-from-slash-command-tool: "true"
---

# Cancel Finesse Execute

To cancel the active Finesse execution loop:

1. Check if `.finesse/loop-state.md` exists using Bash: `test -f .finesse/loop-state.md && echo "EXISTS" || echo "NOT_FOUND"`

2. **If NOT_FOUND**: Say "No active Finesse loop found."

3. **If EXISTS**:
   - Read `.finesse/loop-state.md` to get the current iteration number from the `iteration:` field and the plan name from the `plan_name:` field
   - Read `.finesse/run-log.json` if it exists. Update it:
     - Set `"finished_at"` to the current ISO 8601 timestamp
     - Set `"final_iteration"` to the current iteration value
     - Set `"outcome"` to `"cancelled"`
     - Write the updated JSON back to `.finesse/run-log.json`
   - Remove the state file using Bash: `rm .finesse/loop-state.md`
   - Report: "Cancelled Finesse loop '<plan_name>' at iteration N. Telemetry saved to .finesse/run-log.json."