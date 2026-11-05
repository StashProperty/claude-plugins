# stash-property

10 Australian property skills plus the Stash MCP connector (`https://mcp-api.stashproperty.net/`). Sign in with your own Stash account.

```
/plugin install stash-property --marketplace StashProperty/claude-plugins
```

Full install notes and the skill list are in the [repo README](../../README.md).

The three designed reports use fixed PDF build scripts in `skills/report-export/scripts/`, so every user gets the same layout:

| Report | Skill | Script | Pages |
|---|---|---|---|
| Property Appraisal (for the owner, price on the last page) | cma | build_appraisal.py | 6 |
| Pre-Appraisal Briefing (for the agent) | pre-appraisal | build_briefing.py | 5 |
| Campaign Review / Listing Update (for the vendor) | listing-update | build_campaign_review.py | 9 |

`skills/report-export/examples/` holds sample data, a brand file and reference PDFs.
