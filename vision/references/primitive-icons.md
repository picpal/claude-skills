# Icons (primitive)

A monochrome 24×24 icon library for IT/cloud diagrams. Each icon uses `currentColor` so it inherits ink from its parent SVG and adapts to the editorial skin or any user-onboarded brand palette.

## The two rules


**1 · The icon says what the thing *does*. The label says which product does it.**

A node already carries the product name in bold — `Apache NiFi`, `Trino`, `MinIO / S3`. A brand mark
on the same node repeats that name in a shape most readers cannot decode, and spends the one visual
slot that could have said *what kind of thing this is*. So the node icon is a **function icon**:
`transform`, `query`, `bucket`, `schedule`, `dashboard`, `notebook`.

Reach for a brand mark only when the vendor **is** the subject — a stack inventory, a
tool-comparison table, a "what we run" slide. In an architecture or flow diagram, never.

**2 · One icon style per diagram.**

Stroked and filled marks cannot be optically balanced against each other. A filled silhouette is a
solid mass; a hairline mark of the same 24×24 box carries a fraction of the ink. Put them side by
side and no amount of resizing makes the row read as one system — see
[lessons.md](../lessons.md) → *Optical weight is not a size you can set*.

Every icon in the **Compute · People · Network · Data · Analytics · Kubernetes · Action · DevOps**
categories is stroked and interchangeable. The **Brand · Data stack · Language · Statistical tools**
categories are filled silhouettes; use them together or not at all.

## Usage


Find the icon by name (the `### name` headings below) and copy the fenced `<svg>` snippet.

**Placement — position with `x`/`y` on a nested `<svg>`, not with `<g transform>`:**

```svg
<svg x="440" y="118" width="24" height="24" viewBox="0 0 24 24"
     fill="none" stroke="#2d3142" stroke-width="1.5"
     stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">…paths…</svg>
```

A nested `<svg>` re-establishes the viewport, so the paths land inside the 24×24 box whatever their
own geometry. A `<g transform="translate(…)">` does not: it inherits the parent's user units, and
any icon whose artwork is not already 24-unit scale draws at its native size. Every icon here is
normalised to `viewBox="0 0 24 24"`, so both forms happen to work today — the nested `<svg>` is what
keeps that true when the library grows.

**Geometry contract** — enforced by [`tools/verify-icons.py`](../tools/verify-icons.py):

| | rule | why |
|---|---|---|
| viewBox | exactly `0 0 24 24` | the grid every placement rule assumes |
| box | `width` = `height`, 24 in a node, 20 in a caption or legend | two sizes, so a row never wobbles |
| centre | `icon_cx == node_cx` | the icon hangs off the node's axis, like the label |
| style | all stroked or all filled within one file | rule 2 above |
| stroke | `1.5` at 24px, `1.5` at 20px | hairline, matching the skill's rules and connectors |

**Colour** — set `stroke` (stroked icons) or `fill` (filled marks) to `ink` for a normal node,
`accent` for the focal node, `muted` for a caption or legend glyph. Never both: a stroked icon with
a fill reads as a smudge at 24px.

**Wordmarks.** `spss`, `sas`, `stata`, `pentaho` and `hop` are set type, not drawings — normalised to
the grid they are 24 wide and 6–10 tall. They are legible at 40px and up, in a caption or a table
cell. They are not node icons; at 24px they are a grey bar.

## Index

All 103 icons by name. Copy one with `grep -A6 '^### <name>' references/primitive-icons.md` rather than reading either file whole — the brand file alone is ~24k tokens.

**Function icons — this file.** All stroked, all interchangeable:

- `Compute` — laptop · phone · desktop · server · container · vm · cluster
- `People` — user · users · admin · robot
- `Network` — cloud · internet · cdn · firewall · vpn · load-balancer · gateway · dns
- `Data` — database · file · log · queue · cache · bucket · backup · search · table · warehouse · catalog · stream · query · transfer
- `Analytics` — dashboard · chart · report · notebook · ml
- `Kubernetes` — pod · node · service · deployment · ingress · volume
- `Action` — api · request · response · sync · lock · key · alert · transform · schedule
- `DevOps` — git-branch · terminal · pipeline · bug · monitoring · test · dag · code
- `File formats` — excel · csv · txt

**Brand marks — [primitive-icons-brand.md](primitive-icons-brand.md).** Filled silhouettes; a diagram uses these *or* the set above, never both:

- `Brand` — docker · terraform · aws · azure · github · kubernetes · gcp · postgres · redis · nginx · gitea · keycloak · active-directory · minio · mysql · oracle · sqlserver · sqlite · hive · starrocks
- `Data stack` — nifi · airflow · hop · pentaho · dagster · trino · superset · redash · tableau · powerbi · jupyter
- `Language` — python · r · sql
- `Statistical tools` — spss · sas · stata · rstudio · qgis

## Compute


### laptop
User laptop or workstation.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 19l18 0" /> <path d="M5 7a1 1 0 0 1 1 -1h12a1 1 0 0 1 1 1v8a1 1 0 0 1 -1 1h-12a1 1 0 0 1 -1 -1l0 -8" /></svg>
```

Source: Tabler Icons / `device-laptop` (MIT)

### phone
Mobile phone or tablet client.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 5a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2v-14" /> <path d="M11 4h2" /> <path d="M12 17v.01" /></svg>
```

Source: Tabler Icons / `device-mobile` (MIT)

### desktop
Desktop computer.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a1 1 0 0 1 1 -1h16a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-16a1 1 0 0 1 -1 -1v-10" /> <path d="M7 20h10" /> <path d="M9 16v4" /> <path d="M15 16v4" /></svg>
```

Source: Tabler Icons / `device-desktop` (MIT)

### server
Physical server or VM host.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v2a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3" /> <path d="M3 15a3 3 0 0 1 3 -3h12a3 3 0 0 1 3 3v2a3 3 0 0 1 -3 3h-12a3 3 0 0 1 -3 -3l0 -2" /> <path d="M7 8l0 .01" /> <path d="M7 16l0 .01" /></svg>
```

Source: Tabler Icons / `server` (MIT)

### container
Container image or running instance.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4.5l0 9l-8 4.5l-8 -4.5l0 -9l8 -4.5" /> <path d="M12 12l8 -4.5" /> <path d="M12 12l0 9" /> <path d="M12 12l-8 -4.5" /> <path d="M16 5.25l-8 4.5" /></svg>
```

Source: Tabler Icons / `package` (MIT)

### vm
Virtual machine.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16.008v-8.018a1.98 1.98 0 0 0 -1 -1.717l-7 -4.008a2.016 2.016 0 0 0 -2 0l-7 4.008c-.619 .355 -1 1.01 -1 1.718v8.018c0 .709 .381 1.363 1 1.717l7 4.008a2.016 2.016 0 0 0 2 0l7 -4.008c.619 -.355 1 -1.01 1 -1.718" /> <path d="M12 22v-10" /> <path d="M12 12l8.73 -5.04" /> <path d="M3.27 6.96l8.73 5.04" /></svg>
```

Source: Tabler Icons / `cube` (MIT)

### cluster
Distributed / MPP cluster — many workers, one engine.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 19a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M18 5a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M10 5a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M6 12a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M18 19a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M14 12a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M22 12a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M6 12h4" /> <path d="M14 12h4" /> <path d="M15 7l-2 3" /> <path d="M9 7l2 3" /> <path d="M11 14l-2 3" /> <path d="M13 14l2 3" /></svg>
```

Source: Tabler Icons / `topology-star-3` (MIT)

## People


### user
End user or single actor.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0" /> <path d="M6 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2" /></svg>
```

Source: Tabler Icons / `user` (MIT)

### users
Group / cohort / team.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /> <path d="M3 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2" /> <path d="M16 3.13a4 4 0 0 1 0 7.75" /> <path d="M21 21v-2a4 4 0 0 0 -3 -3.85" /></svg>
```

Source: Tabler Icons / `users` (MIT)

### admin
Privileged user / admin.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 21v-2a4 4 0 0 1 4 -4h2" /> <path d="M22 16c0 4 -2.5 6 -3.5 6s-3.5 -2 -3.5 -6c1 0 2.5 -.5 3.5 -1.5c1 1 2.5 1.5 3.5 1.5" /> <path d="M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0" /></svg>
```

Source: Tabler Icons / `user-shield` (MIT)

### robot
Bot, agent, or automated process.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6a2 2 0 0 1 2 -2h8a2 2 0 0 1 2 2v4a2 2 0 0 1 -2 2h-8a2 2 0 0 1 -2 -2l0 -4" /> <path d="M12 2v2" /> <path d="M9 12v9" /> <path d="M15 12v9" /> <path d="M5 16l4 -2" /> <path d="M15 14l4 2" /> <path d="M9 18h6" /> <path d="M10 8v.01" /> <path d="M14 8v.01" /></svg>
```

Source: Tabler Icons / `robot` (MIT)

## Network


### cloud
Cloud provider or boundary.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6.657 18c-2.572 0 -4.657 -2.007 -4.657 -4.483c0 -2.475 2.085 -4.482 4.657 -4.482c.393 -1.762 1.794 -3.2 3.675 -3.773c1.88 -.572 3.956 -.193 5.444 1c1.488 1.19 2.162 3.007 1.77 4.769h.99c1.913 0 3.464 1.56 3.464 3.486c0 1.927 -1.551 3.487 -3.465 3.487h-11.878" /></svg>
```

Source: Tabler Icons / `cloud` (MIT)

### internet
Public internet.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" /> <path d="M3.6 9h16.8" /> <path d="M3.6 15h16.8" /> <path d="M11.5 3a17 17 0 0 0 0 18" /> <path d="M12.5 3a17 17 0 0 1 0 18" /></svg>
```

Source: Tabler Icons / `world` (MIT)

### cdn
CDN or edge cache.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19.5 7a9 9 0 0 0 -7.5 -4a8.991 8.991 0 0 0 -7.484 4" /> <path d="M11.5 3a16.989 16.989 0 0 0 -1.826 4" /> <path d="M12.5 3a16.989 16.989 0 0 1 1.828 4" /> <path d="M19.5 17a9 9 0 0 1 -7.5 4a8.991 8.991 0 0 1 -7.484 -4" /> <path d="M11.5 21a16.989 16.989 0 0 1 -1.826 -4" /> <path d="M12.5 21a16.989 16.989 0 0 0 1.828 -4" /> <path d="M2 10l1 4l1.5 -4l1.5 4l1 -4" /> <path d="M17 10l1 4l1.5 -4l1.5 4l1 -4" /> <path d="M9.5 10l1 4l1.5 -4l1.5 4l1 -4" /></svg>
```

Source: Tabler Icons / `world-www` (MIT)

### firewall
Firewall or perimeter control.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2l0 -12" /> <path d="M4 8h16" /> <path d="M20 12h-16" /> <path d="M4 16h16" /> <path d="M9 4v4" /> <path d="M14 8v4" /> <path d="M8 12v4" /> <path d="M16 12v4" /> <path d="M11 16v4" /></svg>
```

Source: Tabler Icons / `wall` (MIT)

### vpn
VPN or encrypted tunnel.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a12 12 0 0 0 8.5 3a12 12 0 0 1 -8.5 15a12 12 0 0 1 -8.5 -15a12 12 0 0 0 8.5 -3" /> <path d="M11 11a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" /> <path d="M12 12l0 2.5" /></svg>
```

Source: Tabler Icons / `shield-lock` (MIT)

### load-balancer
Load balancer / traffic split.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 17h-8l-3.5 -5h-6.5" /> <path d="M21 7h-8l-3.495 5" /> <path d="M18 10l3 -3l-3 -3" /> <path d="M18 20l3 -3l-3 -3" /></svg>
```

Source: Tabler Icons / `arrows-split` (MIT)

### gateway
API gateway or ingress door.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 12v.01" /> <path d="M3 21h18" /> <path d="M5 21v-16a2 2 0 0 1 2 -2h6m4 10.5v7.5" /> <path d="M21 7h-7m3 -3l-3 3l3 3" /></svg>
```

Source: Tabler Icons / `door-enter` (MIT)

### dns
DNS / name resolution.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6.5 7.5a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" /> <path d="M3 6v5.172a2 2 0 0 0 .586 1.414l7.71 7.71a2.41 2.41 0 0 0 3.408 0l5.592 -5.592a2.41 2.41 0 0 0 0 -3.408l-7.71 -7.71a2 2 0 0 0 -1.414 -.586h-5.172a3 3 0 0 0 -3 3" /></svg>
```

Source: Tabler Icons / `tag` (MIT)

## Data


### database
Relational or document database.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a8 3 0 1 0 16 0a8 3 0 1 0 -16 0" /> <path d="M4 6v6a8 3 0 0 0 16 0v-6" /> <path d="M4 12v6a8 3 0 0 0 16 0v-6" /></svg>
```

Source: Tabler Icons / `database` (MIT)

### file
Generic file.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3v4a1 1 0 0 0 1 1h4" /> <path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2" /></svg>
```

Source: Tabler Icons / `file` (MIT)

### log
Log file / event stream.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3v4a1 1 0 0 0 1 1h4" /> <path d="M17 21h-10a2 2 0 0 1 -2 -2v-14a2 2 0 0 1 2 -2h7l5 5v11a2 2 0 0 1 -2 2" /> <path d="M9 9l1 0" /> <path d="M9 13l6 0" /> <path d="M9 17l6 0" /></svg>
```

Source: Tabler Icons / `file-text` (MIT)

### queue
Message queue, buffered stream, or layered storage (bronze / silver / gold).

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4l-8 4l8 4l8 -4l-8 -4" /> <path d="M4 12l8 4l8 -4" /> <path d="M4 16l8 4l8 -4" /></svg>
```

Source: Tabler Icons / `stack-2` (MIT)

### cache
Cache layer.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3l0 7l6 0l-8 11l0 -7l-6 0l8 -11" /></svg>
```

Source: Tabler Icons / `bolt` (MIT)

### bucket
Object storage / S3 bucket.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7a8 4 0 1 0 16 0a8 4 0 1 0 -16 0" /> <path d="M4 7c0 .664 .088 1.324 .263 1.965l2.737 10.035c.5 1.5 2.239 2 5 2s4.5 -.5 5 -2c.333 -1 1.246 -4.345 2.737 -10.035a7.45 7.45 0 0 0 .263 -1.965" /></svg>
```

Source: Tabler Icons / `bucket` (MIT)

### backup
Backup or snapshot.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4h10l4 4v10a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2" /> <path d="M10 14a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M14 4l0 4l-6 0l0 -4" /></svg>
```

Source: Tabler Icons / `device-floppy` (MIT)

### search
Search index / query.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10a7 7 0 1 0 14 0a7 7 0 1 0 -14 0" /> <path d="M21 21l-6 -6" /></svg>
```

Source: Tabler Icons / `search` (MIT)

### table
Table or dataset.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v14a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2v-14" /> <path d="M3 10h18" /> <path d="M10 3v18" /></svg>
```

Source: Tabler Icons / `table` (MIT)

### warehouse
Data warehouse — modelled, governed storage.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21v-13l9 -4l9 4v13" /> <path d="M13 13h4v8h-10v-6h6" /> <path d="M13 21v-9a1 1 0 0 0 -1 -1h-2a1 1 0 0 0 -1 1v3" /></svg>
```

Source: Tabler Icons / `building-warehouse` (MIT)

### catalog
Data catalog / metadata registry.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 5h8" /> <path d="M13 9h5" /> <path d="M13 15h8" /> <path d="M13 19h5" /> <path d="M3 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4" /> <path d="M3 15a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v4a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -4" /></svg>
```

Source: Tabler Icons / `list-details` (MIT)

### stream
Streaming or real-time feed.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12h-2c-.894 0 -1.662 -.857 -1.761 -2c-.296 -3.45 -.749 -6 -2.749 -6s-2.5 3.582 -2.5 8s-.5 8 -2.5 8s-2.452 -2.547 -2.749 -6c-.1 -1.147 -.867 -2 -1.763 -2h-2" /></svg>
```

Source: Tabler Icons / `wave-sine` (MIT)

### query
Query engine — SQL over stored data.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6c0 1.657 3.582 3 8 3s8 -1.343 8 -3s-3.582 -3 -8 -3s-8 1.343 -8 3" /> <path d="M4 6v6c0 1.657 3.582 3 8 3m8 -3.5v-5.5" /> <path d="M4 12v6c0 1.657 3.582 3 8 3" /> <path d="M15 18a3 3 0 1 0 6 0a3 3 0 1 0 -6 0" /> <path d="M20.2 20.2l1.8 1.8" /></svg>
```

Source: Tabler Icons / `database-search` (MIT)

### transfer
File transfer — FTP / SFTP / batch drop.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10h-16l5.5 -6" /> <path d="M4 14h16l-5.5 6" /></svg>
```

Source: Tabler Icons / `transfer` (MIT)

## Analytics


### dashboard
BI dashboard.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1" /> <path d="M5 16h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1" /> <path d="M15 12h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1" /> <path d="M15 4h4a1 1 0 0 1 1 1v2a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1v-2a1 1 0 0 1 1 -1" /></svg>
```

Source: Tabler Icons / `layout-dashboard` (MIT)

### chart
Chart or metric.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 13a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -6" /> <path d="M15 9a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -10" /> <path d="M9 5a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-4a1 1 0 0 1 -1 -1l0 -14" /> <path d="M4 20h14" /></svg>
```

Source: Tabler Icons / `chart-bar` (MIT)

### report
Report — a document built from data.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2" /> <path d="M9 5a2 2 0 0 1 2 -2h2a2 2 0 0 1 2 2a2 2 0 0 1 -2 2h-2a2 2 0 0 1 -2 -2" /> <path d="M9 17v-5" /> <path d="M12 17v-1" /> <path d="M15 17v-3" /></svg>
```

Source: Tabler Icons / `report-analytics` (MIT)

### notebook
Notebook — interactive exploration.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4h11a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-11a1 1 0 0 1 -1 -1v-14a1 1 0 0 1 1 -1m3 0v18" /> <path d="M13 8l2 0" /> <path d="M13 12l2 0" /></svg>
```

Source: Tabler Icons / `notebook` (MIT)

### ml
Model training / machine learning.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 13a3.5 3.5 0 0 0 -3.5 3.5v1a3.5 3.5 0 0 0 7 0v-1.8" /> <path d="M8.5 13a3.5 3.5 0 0 1 3.5 3.5v1a3.5 3.5 0 0 1 -7 0v-1.8" /> <path d="M17.5 16a3.5 3.5 0 0 0 0 -7h-.5" /> <path d="M19 9.3v-2.8a3.5 3.5 0 0 0 -7 0" /> <path d="M6.5 16a3.5 3.5 0 0 1 0 -7h.5" /> <path d="M5 9.3v-2.8a3.5 3.5 0 0 1 7 0v10" /></svg>
```

Source: Tabler Icons / `brain` (MIT)

## Kubernetes


### pod
Pod (smallest deployable unit).

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19.875 6.27a2.225 2.225 0 0 1 1.125 1.948v7.284c0 .809 -.443 1.555 -1.158 1.948l-6.75 4.27a2.269 2.269 0 0 1 -2.184 0l-6.75 -4.27a2.225 2.225 0 0 1 -1.158 -1.948v-7.285c0 -.809 .443 -1.554 1.158 -1.947l6.75 -3.98a2.33 2.33 0 0 1 2.25 0l6.75 3.98h-.033" /></svg>
```

Source: Tabler Icons / `hexagon` (MIT)

### node
Cluster node.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 18a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M20 6a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M8 6a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M20 18a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M14 12a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M7.5 7.5l3 3" /> <path d="M7.5 16.5l3 -3" /> <path d="M13.5 13.5l3 3" /> <path d="M16.5 7.5l-3 3" /></svg>
```

Source: Tabler Icons / `topology-star` (MIT)

### service
K8s service / virtual endpoint.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 0 -8.979 9" /> <path d="M3.6 9h16.8" /> <path d="M3.6 15h8.9" /> <path d="M11.5 3a17 17 0 0 0 0 18" /> <path d="M12.5 3a16.992 16.992 0 0 1 2.522 10.376" /> <path d="M17.001 19a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M19.001 15.5v1.5" /> <path d="M19.001 21v1.5" /> <path d="M22.032 17.25l-1.299 .75" /> <path d="M17.27 20l-1.3 .75" /> <path d="M15.97 17.25l1.3 .75" /> <path d="M20.733 20l1.3 .75" /></svg>
```

Source: Tabler Icons / `world-cog` (MIT)

### deployment
Deployment rollout.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 13a8 8 0 0 1 7 7a6 6 0 0 0 3 -5a9 9 0 0 0 6 -8a3 3 0 0 0 -3 -3a9 9 0 0 0 -8 6a6 6 0 0 0 -5 3" /> <path d="M7 14a6 6 0 0 0 -3 6a6 6 0 0 0 6 -3" /> <path d="M14 9a1 1 0 1 0 2 0a1 1 0 1 0 -2 0" /></svg>
```

Source: Tabler Icons / `rocket` (MIT)

### ingress
Ingress controller / route in.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12h13" /> <path d="M18 9l3 3l-3 3" /> <path d="M5.5 9.5l-2.5 2.5l2.5 2.5l2.5 -2.5l-2.5 -2.5" /></svg>
```

Source: Tabler Icons / `arrow-right-rhombus` (MIT)

### volume
Persistent volume.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 21h10a2 2 0 0 0 2 -2v-14a2 2 0 0 0 -2 -2h-6.172a2 2 0 0 0 -1.414 .586l-3.828 3.828a2 2 0 0 0 -.586 1.414v10.172a2 2 0 0 0 2 2" /> <path d="M13 6v2" /> <path d="M16 6v2" /> <path d="M10 7v1" /></svg>
```

Source: Tabler Icons / `device-sd-card` (MIT)

## Action


### api
API surface / endpoint.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4a2 2 0 0 0 -2 2v3a2 3 0 0 1 -2 3a2 3 0 0 1 2 3v3a2 2 0 0 0 2 2" /> <path d="M17 4a2 2 0 0 1 2 2v3a2 3 0 0 0 2 3a2 3 0 0 0 -2 3v3a2 2 0 0 1 -2 2" /></svg>
```

Source: Tabler Icons / `braces` (MIT)

### request
Outbound request.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l14 0" /> <path d="M13 18l6 -6" /> <path d="M13 6l6 6" /></svg>
```

Source: Tabler Icons / `arrow-right` (MIT)

### response
Inbound response.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l14 0" /> <path d="M5 12l6 6" /> <path d="M5 12l6 -6" /></svg>
```

Source: Tabler Icons / `arrow-left` (MIT)

### sync
Sync / reconcile loop.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4" /> <path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" /></svg>
```

Source: Tabler Icons / `refresh` (MIT)

### lock
Locked / authenticated.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v6a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2v-6" /> <path d="M11 16a1 1 0 1 0 2 0a1 1 0 0 0 -2 0" /> <path d="M8 11v-4a4 4 0 1 1 8 0v4" /></svg>
```

Source: Tabler Icons / `lock` (MIT)

### key
Key / secret.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16.555 3.843l3.602 3.602a2.877 2.877 0 0 1 0 4.069l-2.643 2.643a2.877 2.877 0 0 1 -4.069 0l-.301 -.301l-6.558 6.558a2 2 0 0 1 -1.239 .578l-.175 .008h-1.172a1 1 0 0 1 -.993 -.883l-.007 -.117v-1.172a2 2 0 0 1 .467 -1.284l.119 -.13l.414 -.414h2v-2h2v-2l2.144 -2.144l-.301 -.301a2.877 2.877 0 0 1 0 -4.069l2.643 -2.643a2.877 2.877 0 0 1 4.069 0" /> <path d="M15 9h.01" /></svg>
```

Source: Tabler Icons / `key` (MIT)

### alert
Warning / paged alert.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4" /> <path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0" /> <path d="M12 16h.01" /></svg>
```

Source: Tabler Icons / `alert-triangle` (MIT)

### transform
Transform — reshape or route records (ETL).

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" /> <path d="M21 11v-3a2 2 0 0 0 -2 -2h-6l3 3m0 -6l-3 3" /> <path d="M3 13v3a2 2 0 0 0 2 2h6l-3 -3m0 6l3 -3" /> <path d="M15 18a3 3 0 1 0 6 0a3 3 0 0 0 -6 0" /></svg>
```

Source: Tabler Icons / `transform` (MIT)

### schedule
Scheduled run / orchestration trigger.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 21h-4.5a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v3" /> <path d="M16 3v4" /> <path d="M8 3v4" /> <path d="M4 11h10" /> <path d="M14 18a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /> <path d="M18 16.5v1.5l.5 .5" /></svg>
```

Source: Tabler Icons / `calendar-clock` (MIT)

## DevOps


### git-branch
Branch / fork point.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 18a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M5 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M15 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M7 8l0 8" /> <path d="M9 18h6a2 2 0 0 0 2 -2v-5" /> <path d="M14 14l3 -3l3 3" /></svg>
```

Source: Tabler Icons / `git-branch` (MIT)

### terminal
Shell / CLI.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7l5 5l-5 5" /> <path d="M12 19l7 0" /></svg>
```

Source: Tabler Icons / `terminal` (MIT)

### pipeline
CI/CD pipeline.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 18a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M5 6a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M15 12a2 2 0 1 0 4 0a2 2 0 1 0 -4 0" /> <path d="M7 8l0 8" /> <path d="M7 8a4 4 0 0 0 4 4h4" /></svg>
```

Source: Tabler Icons / `git-merge` (MIT)

### bug
Bug / defect.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 9v-1a3 3 0 0 1 6 0v1" /> <path d="M8 9h8a6 6 0 0 1 1 3v3a5 5 0 0 1 -10 0v-3a6 6 0 0 1 1 -3" /> <path d="M3 13l4 0" /> <path d="M17 13l4 0" /> <path d="M12 20l0 -6" /> <path d="M4 19l3.35 -2" /> <path d="M20 19l-3.35 -2" /> <path d="M4 7l3.75 2.4" /> <path d="M20 7l-3.75 2.4" /></svg>
```

Source: Tabler Icons / `bug` (MIT)

### monitoring
Metrics / observability.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19l16 0" /> <path d="M4 15l4 -6l4 2l4 -5l4 4" /></svg>
```

Source: Tabler Icons / `chart-line` (MIT)

### test
Test / experiment.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 8.04l-12.122 12.124a2.857 2.857 0 1 1 -4.041 -4.04l12.122 -12.124" /> <path d="M7 13h8" /> <path d="M19 15l1.5 1.6a2 2 0 1 1 -3 0l1.5 -1.6" /> <path d="M15 3l6 6" /></svg>
```

Source: Tabler Icons / `test-pipe` (MIT)

### dag
Workflow DAG — ordered, branching task graph.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 20a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M16 4a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M16 20a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M11 12a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M21 12a2 2 0 1 0 -4 0a2 2 0 0 0 4 0" /> <path d="M5.058 18.306l2.88 -4.606" /> <path d="M10.061 10.303l2.877 -4.604" /> <path d="M10.065 13.705l2.876 4.6" /> <path d="M15.063 5.7l2.881 4.61" /></svg>
```

Source: Tabler Icons / `binary-tree` (MIT)

### code
Script or batch job.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 8l-4 4l4 4" /> <path d="M17 8l4 4l-4 4" /> <path d="M14 4l-4 16" /></svg>
```

Source: Tabler Icons / `code` (MIT)

## File formats


### excel
Microsoft Excel spreadsheet.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3v4a1 1 0 0 0 1 1h4" /> <path d="M5 12v-7a2 2 0 0 1 2 -2h7l5 5v4" /> <path d="M4 15l4 6" /> <path d="M4 21l4 -6" /> <path d="M17 20.25c0 .414 .336 .75 .75 .75h1.25a1 1 0 0 0 1 -1v-1a1 1 0 0 0 -1 -1h-1a1 1 0 0 1 -1 -1v-1a1 1 0 0 1 1 -1h1.25a.75 .75 0 0 1 .75 .75" /> <path d="M11 15v6h3" /></svg>
```

Source: Tabler Icons / `file-type-xls` (MIT)

### csv
Comma-separated values file.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3v4a1 1 0 0 0 1 1h4" /> <path d="M5 12v-7a2 2 0 0 1 2 -2h7l5 5v4" /> <path d="M7 16.5a1.5 1.5 0 0 0 -3 0v3a1.5 1.5 0 0 0 3 0" /> <path d="M10 20.25c0 .414 .336 .75 .75 .75h1.25a1 1 0 0 0 1 -1v-1a1 1 0 0 0 -1 -1h-1a1 1 0 0 1 -1 -1v-1a1 1 0 0 1 1 -1h1.25a.75 .75 0 0 1 .75 .75" /> <path d="M16 15l2 6l2 -6" /></svg>
```

Source: Tabler Icons / `file-type-csv` (MIT)

### txt
Plain text file.

```svg
<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3v4a1 1 0 0 0 1 1h4" /> <path d="M14 3v4a1 1 0 0 0 1 1h4" /> <path d="M16.5 15h3" /> <path d="M5 12v-7a2 2 0 0 1 2 -2h7l5 5v4" /> <path d="M4.5 15h3" /> <path d="M6 15v6" /> <path d="M18 15v6" /> <path d="M10 15l4 6" /> <path d="M10 21l4 -6" /></svg>
```

Source: Tabler Icons / `file-type-txt` (MIT)

---

## License attribution


- **Tabler Icons** — MIT — https://github.com/tabler/tabler-icons
- **Simple Icons** — CC0 — https://github.com/simple-icons/simple-icons
- **Devicon** — MIT — https://github.com/devicons/devicon
- **log-z/logos** — MIT — https://github.com/log-z/logos

All libraries' licenses permit redistribution, including in this repository's MIT-licensed source. Brand logos retain their respective trademarks; this set is for documentation and illustrative use only.
