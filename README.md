# GoFigr Skills

Claude Code plugin marketplace for [GoFigr](https://gofigr.io) — a reproducibility engine that versions figures together with the code, data, and environment that produced them.

## Install

### Claude Code

```
/plugin marketplace add GoFigr/skills
/plugin install gofigr@gofigr
```

### claude.ai, Claude Science, and the Skills API

These surfaces take a skill archive rather than a plugin marketplace, and skills
do not sync between surfaces — upload separately wherever you want the skill.

```bash
./scripts/build-zip.sh    # writes dist/gofigr.zip
```

Then upload `dist/gofigr.zip`: in claude.ai under Settings > Capabilities, or via
the `/v1/skills` endpoints for the API. The archive root is the `gofigr/` folder
itself, which is what these uploaders expect.

The skill is plain instructions and reference markdown — no scripts, no network
calls, no package installation — so it works under the sandboxed runtimes on
these surfaces as well as it does in Claude Code.

## What's included

### `gofigr`

Teaches Claude to write correct GoFigr code in Python and R:

- **Figure capture** — automatic capture in Jupyter, `Publisher` in scripts, explicit `publish()` in R
- **Clean Room** — `@reproducible` in Python and `reproducible()` in R, including parameter widgets and interactive mode
- **Asset tracking** — checksummed data reads that link files to the figures they produced

The skill loads automatically when Claude sees GoFigr code or a request to publish a figure. In Claude Code you can also invoke it directly with `/gofigr`.

Targets `gofigr` (Python) ≥ 2.3.3 and `gofigR` (R) ≥ 2.0.2.

It follows the [Agent Skills](https://agentskills.io) open standard: `SKILL.md`
carries only the standard `name` and `description` fields, and bundled files are
referenced by relative path, so it behaves the same on every surface. The
`when_to_use` field is a Claude Code extension that other surfaces ignore, so
every trigger that matters is also in `description`.

## Note on R

Automatic figure capture in R is being sunset. It works by reassigning `plot()` and `print()` in the global environment, which is not reliable. The skill instructs Claude to use an explicit `publish()` call for every R figure, and to convert existing auto-capture code when it encounters it.

Python auto-capture in Jupyter is unaffected and remains the default.

## Documentation

Full docs: <https://gofigr.io/docs>

## License

MIT — see [LICENSE](LICENSE).
