# stash-property

10 Australian property skills plus the Stash MCP connector (`https://mcp-api.stashproperty.net/`). Sign in with your own Stash account.

```
/plugin install stash-property --marketplace StashProperty/claude-plugins
```

Full install notes and the skill list are in the [repo README](../../README.md).

The plugin ships no code. Claude builds the three designed reports with ReportLab from the layout spec in `skills/report-export/SKILL.md`:

| Report | Skill | Pages |
|---|---|---|
| Property Appraisal (for the owner, price on the last page) | cma | 6 |
| Pre-Appraisal Briefing (for the agent) | pre-appraisal | 5 |
| Campaign Review / Listing Update (for the vendor) | listing-update | 9 |

`skills/report-export/examples/` holds sample data and a brand file.
