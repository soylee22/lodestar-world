#!/usr/bin/env python3
"""Synchronise lodestar-world files to atlas-stock-screener/static."""

import shutil
from pathlib import Path

src_dir = Path("/Users/leeslater/lodestar-world")
dst_dir = Path("/Users/leeslater/projects/atlas-stock-screener/static")

# 1. Copy data.js -> lodestar-data.js
shutil.copyfile(src_dir / "data.js", dst_dir / "lodestar-data.js")
print(f"Copied {src_dir / 'data.js'} -> {dst_dir / 'lodestar-data.js'} ({dst_dir / 'lodestar-data.js'} size: {(dst_dir / 'lodestar-data.js').stat().st_size / 1024:.1f} KB)")

# Copy assets to Atlas root assets
if (src_dir / "assets").is_dir():
    shutil.copytree(src_dir / "assets", dst_dir.parent / "assets", dirs_exist_ok=True)
    print("Synchronised company logos to Atlas root assets")

# 2. Build lodestar.html from index.html
html = (src_dir / "index.html").read_text(encoding="utf-8")

# Title and favicon
html = html.replace(
    "<title>Lodestar World — Global Factor and Dividend Rotation</title>",
    "<title>Atlas | Lodestar World — Global Factor and Dividend Rotation</title>\n<link rel=\"icon\" href=\"/static/favicon.svg\" type=\"image/svg+xml\">"
)

# Topbar CSS
topbar_css = """
/* Atlas global universe navigation bar */
.atlas-topbar{
  background:var(--surface);
  border-bottom:1px solid var(--rule);
  font-family:var(--sans);
}
.atlas-topbar .wrap{
  display:flex; align-items:center; justify-content:space-between;
  gap:16px; min-height:52px; padding-block:8px; flex-wrap:wrap;
}
.atlas-brand{
  display:inline-flex; align-items:center; gap:9px;
  text-decoration:none; color:var(--ink); font-weight:600;
  font-size:17px; letter-spacing:-.02em; white-space:nowrap;
}
.atlas-brandmark{
  width:28px; height:28px; border-radius:7px;
  background:var(--ink); color:var(--surface);
  display:inline-flex; align-items:center; justify-content:center;
  font-size:13px; font-weight:700;
}
.atlas-dot{color:var(--s1)}
.atlas-nav{
  display:flex; align-items:center; gap:4px; overflow-x:auto;
  scrollbar-width:none;
}
.atlas-nav::-webkit-scrollbar{display:none}
.atlas-nav a{
  font-size:12px; font-weight:600; color:var(--ink-2);
  text-decoration:none; padding:6px 11px; border-radius:6px;
  white-space:nowrap; transition:background .15s, color .15s;
}
.atlas-nav a:hover{color:var(--ink); background:var(--paper-2)}
.atlas-nav a[aria-current="page"]{
  background:color-mix(in srgb, var(--s1) 14%, transparent);
  color:var(--s1);
}
.atlas-badge{
  font-family:var(--mono); font-size:10.5px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--muted); white-space:nowrap;
}
@media print{ .atlas-topbar{display:none} }
"""
html = html.replace("</style>", topbar_css + "\n</style>")

# Topbar HTML
topbar_html = """
<div class="atlas-topbar" role="navigation" aria-label="Atlas universe navigation">
  <div class="wrap">
    <div style="display:flex;align-items:center;gap:16px;min-width:0;flex-wrap:wrap">
      <a class="atlas-brand" href="/" aria-label="Atlas home">
        <span class="atlas-brandmark">A</span>
        <span>ATLAS<span class="atlas-dot">.</span></span>
      </a>
      <nav class="atlas-nav" aria-label="Asset universe">
        <a href="/">Stocks</a>
        <a href="/etfs.html">ETFs, ETPs &amp; Investment Trusts</a>
        <a href="/transatlantic.html">Transatlantic 50</a>
        <a href="/winner.html">Last Year's Winner</a>
        <a href="/optimal.html">Optimal Div Growth</a>
        <a href="/lodestar.html" aria-current="page">Lodestar World</a>
      </nav>
    </div>
    <span class="atlas-badge">GBP Total Return · LSE UCITS</span>
  </div>
</div>
"""
html = html.replace("<body>\n", "<body>\n" + topbar_html)

# Script src
html = html.replace('<script src="data.js?v=3"></script>', '<script src="/static/lodestar-data.js"></script>')
html = html.replace('<script src="data.js"></script>', '<script src="/static/lodestar-data.js"></script>')

(dst_dir / "lodestar.html").write_text(html, encoding="utf-8")
print(f"Generated {dst_dir / 'lodestar.html'} ({len(html)} bytes)")
