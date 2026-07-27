# GoFigr Skills

Claude Code plugin marketplace for [GoFigr](https://gofigr.io) — a reproducibility engine that versions figures together with the code, data, and environment that produced them.

## Install

```
/plugin marketplace add GoFigr/skills
/plugin install gofigr@gofigr
```

## What's included

### `gofigr`

Teaches Claude to write correct GoFigr code in Python and R:

- **Figure capture** — automatic capture in Jupyter, `Publisher` in scripts, explicit `publish()` in R
- **Clean Room** — `@reproducible` in Python and `reproducible()` in R, including parameter widgets and interactive mode
- **Asset tracking** — checksummed data reads that link files to the figures they produced

The skill loads automatically when Claude sees GoFigr code or a request to publish a figure. You can also invoke it directly with `/gofigr`.

Targets `gofigr` (Python) ≥ 2.3.3 and `gofigR` (R) ≥ 2.0.2.

## Note on R

Automatic figure capture in R is being sunset. It works by reassigning `plot()` and `print()` in the global environment, which is not reliable. The skill instructs Claude to use an explicit `publish()` call for every R figure, and to convert existing auto-capture code when it encounters it.

Python auto-capture in Jupyter is unaffected and remains the default.

## Documentation

Full docs: <https://gofigr.io/docs>

## License

MIT — see [LICENSE](LICENSE).
