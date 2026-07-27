# GoFigr — Python

Package: `gofigr` (pip install gofigr). Verified against 2.3.3.

## Configuration

One-time, interactive:

```bash
gfconfig             # writes ~/.gofigr
gfconfig --advanced  # also sets API URL, auto-publish default, default metadata
```

Or environment variables (no config file needed):

`GF_API_KEY`, or `GF_USERNAME` + `GF_PASSWORD`; plus optional `GF_WORKSPACE`, `GF_ANALYSIS`, `GF_URL`, `GF_AUTO_PUBLISH`.

Never write an API key into a source file.

## Jupyter

```python
%load_ext gofigr
```

That is the whole setup when `~/.gofigr` exists. The extension auto-configures: default workspace from `gfconfig`, an analysis named after the notebook, `auto_publish=True`. Every figure produced in the notebook is captured automatically — no `publish()` call needed.

The magic injects these names into the notebook namespace, so a notebook cell can use them without importing:

`gf` (the `GoFigr` client), `configure`, `publish`, `get_extension`, `FindByName`, `ApiId`, `NotebookName`, `reproducible`, `SliderParam`, `DropdownParam`, `CheckboxParam`, `TextParam`, `StaticParam`.

In a `.py` file, import them instead — see "Scripts" below.

### configure()

Only needed to override defaults. Call it after `%load_ext gofigr`.

```python
from gofigr.jupyter import configure, FindByName, ApiId, NotebookName

configure(
    workspace=FindByName("Primary Workspace", create=False),
    analysis=FindByName("My Analysis", create=True),
    auto_publish=True,
    default_metadata={"study": "Pivotal Trial 1"},
)
```

Selected parameters:

| Parameter | Default | Notes |
|---|---|---|
| `workspace` | from `~/.gofigr` | `FindByName(name, create=False)`, `ApiId(uuid)`, or a UUID string |
| `analysis` | `NotebookName()` | also accepts `FindByName(..., create=True)` or `ApiId(...)` |
| `auto_publish` | `True` | `False` means you call `publish()` yourself |
| `auto_assign` | `False` | server assigns revisions to figures by image content; requires AI enabled server-side |
| `default_metadata` | `None` | dict attached to every revision |
| `watermark` | `DefaultWatermark()` | QR watermark generator |
| `show_watermark` | `True` | `False` displays the unmodified figure; the watermarked version is still published |
| `save_pickle` | `True` | also stores the figure as a pickle, enabling `load_pickled_figure()` |
| `widget_class` | `DetailedWidget` | or `CompactWidget` |

`FindByName(name, create=False)` defaults to *not* creating. Pass `create=True` when the analysis may not exist yet.

### Manual publishing

With `auto_publish=False`:

```python
from gofigr.jupyter import publish, FindByName
import matplotlib.pyplot as plt

plt.plot([1, 2, 3, 4], [1, 4, 9, 16])
publish(fig=plt.gcf(), target=FindByName("Quadratic", create=True))
```

`publish()` with no arguments publishes the default figure across all available backends.

## Scripts

Outside Jupyter there is no extension and no auto-capture. Use `Publisher`:

```python
import matplotlib.pyplot as plt
from gofigr.publisher import Publisher

pub = Publisher(workspace="My Workspace", analysis="Script Analysis")

plt.plot(range(10), [i ** 2 for i in range(10)])
plt.title("Quadratic")
pub.publish(plt.gcf())
```

Credentials come from `~/.gofigr` or the environment. `Publisher` also accepts `gf=GoFigr(...)`, `watermark`, `show_watermark`, `image_formats`, `default_metadata`, `save_pickle`, `widget_class`, `auto_assign`.

### Publisher.publish()

```python
pub.publish(
    fig=None,              # defaults to plt.gcf()
    target=None,           # gf.Figure, API ID, or FindByName; ignored when auto_assign=True
    dataframes=None,       # dict of name -> DataFrame, published with the figure
    metadata=None,         # dict attached to this revision
    backend=None,          # inferred from figure type if omitted
    files=None,            # list of paths, or dict of name -> path/file object
    auto_assign=None,      # None uses the Publisher's default
)
```

Returns a `FigureRevision`. With `auto_assign=True` the revision has `is_processing=True` until the server finishes; call `revision.wait_for_processing()` if you need to block.

Backends are inferred, so matplotlib, seaborn (matplotlib under the hood), and plotly figures all work:

```python
import plotly.express as px
fig = px.scatter(df, x="a", y="b")
pub.publish(fig)
```

## Asset tracking

Reading data through GoFigr checksums it, uploads it if new, and links the resulting asset revision to every figure published afterwards.

```python
df = gf.read_csv("data/penguins.csv")   # Jupyter: gf is already in the namespace
```

```python
from gofigr import GoFigr
gf = GoFigr()                            # scripts
df = gf.read_csv("data/penguins.csv")
```

Available readers, all with the same signature as their pandas counterparts:

`read_csv`, `read_excel`, `read_json`, `read_html`, `read_parquet`, `read_feather`, `read_hdf`, `read_pickle`, `read_sas`

The returned DataFrame carries the revision ID in `df.attrs["_gofigr_revision"]`.

Other entry points:

```python
gf.sync.sync("data/penguins.csv")            # sync without reading
with gf.sync.open("data/raw.txt") as f: ...  # drop-in for open()
gf.sync.revisions                            # every asset revision synced this session
```

Only swap in a GoFigr reader where the file genuinely feeds the analysis. Rewriting every `pd.read_csv` in a codebase is rarely what the user wants — ask first if it is more than a few call sites.

## Troubleshooting

**Figures don't appear.** Check `auto_publish` is `True` and that `%load_ext gofigr` ran before the plotting cells. The extension registers a display hook at load time; figures produced by cells that ran earlier are not captured retroactively.

**"GoFigr authentication failed"** on `%load_ext`. The saved key is invalid or revoked. Re-run `gfconfig`, or call `configure(api_key=...)` manually.

**Auto-configuration didn't happen.** `%load_ext gofigr` only auto-configures when a config file or credentials exist. Otherwise call `configure()` explicitly.
