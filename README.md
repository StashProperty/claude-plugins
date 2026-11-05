# Stash Property Claude plugins

Claude plugins from [Stash Property](https://www.stashproperty.com.au): Australian property valuations, appraisals and reports built on live Stash data.

## stash-property

One install gives you 10 property skills and the Stash MCP connector.

### Install (Claude Code)

```
/plugin install stash-property --marketplace StashProperty/claude-plugins
```

On Claude Code older than 2.1.275, use two steps instead:

```
/plugin marketplace add StashProperty/claude-plugins
/plugin install stash-property@stash
```

When it asks, sign in to the **Stash** connector with your own Stash account. You'll need an active Stash plan that includes AI access. Restart Claude Code if the skills don't appear straight away.

### Install (Claude desktop / claude.ai)

Go to **Settings → Plugins → Add marketplace**, enter `StashProperty/claude-plugins`, then install **stash-property**.

### Already added the Stash connector from the Claude directory?

The plugin includes the same connector (`https://mcp-api.stashproperty.net/`), so you may see Stash listed twice. Keep one and switch the other off. Both work the same way.

### What's inside

| Skill | What it does |
|---|---|
| cma | Quickval, then a buyer CMA, a 6-page seller Property Appraisal, or the full vendor CMA |
| pre-appraisal | Agent briefing before the listing appointment, with no price decided |
| listing-update | Campaign Review for a listing that isn't selling (Day N) |
| commercial-cma | Commercial and industrial CMA |
| feaso | Development and subdivision feasibility, with an optional Excel model |
| reno-case-studies | Repeat-sale case studies: flip, reno, knockdown-rebuild |
| find-on-market-deals | Ranked live listings |
| find-suburbs | Ranked suburbs by strategy |
| planning | Council planning rules |
| report-export | Shared step: PDF, Word or Canva output in Stash branding or yours |

The PDF reports need Python 3 with `reportlab` and `pillow`. Claude installs them if they're missing.

### Try these

- "Quick val for 12 Smith St, Bulimba"
- "Property appraisal for the seller of 12 Smith St, Bulimba, as a PDF"
- "Pre-appraisal for 12 Smith St, Bulimba. Canva, my brand: https://myagency.com.au"
- "Make a sample appraisal with a fake address in Camp Hill so I can show clients"

## Updating

To get the latest version, run `/plugin marketplace update stash`. Maintainers: bump `version` in `plugins/stash-property/.claude-plugin/plugin.json` with every change, then tag the release as `vX.Y.Z`.

## Privacy

See the [Stash privacy policy](https://www.stashproperty.com.au/privacy/) (section 14 covers the Stash MCP and AI assistant integrations).

## Support

support@stashproperty.com.au
