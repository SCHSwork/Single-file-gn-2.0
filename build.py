#!/usr/bin/env python3
"""Build a single-file version of GN 2.0.

Reads a checkout of SCHSwork/math and writes one index.html with every CSS file,
JS file, config JSON and icon inlined. Nothing else is needed to run the site:
it can be opened straight from disk (file://), hosted anywhere, or shared as
one file.

Usage:
    python3 build.py <path to SCHSwork/math checkout> [output file]
"""
import base64
import json
import re
import sys
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "math")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "index.html")

# Config files the site fetches with relative URLs; served from inside the page
EMBEDDED_FILES = [
    "config/library-pinned.json",
    "config/game-info.json",
    "config/partner-games.json",
    "config/partner-games-playgama.json",
    "config/owner-settings.json",
]
# Scripts that only make sense for a hosted multi-file site
SKIP_SCRIPTS = {"js/service-worker-setup.js"}


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode((SRC / path).read_bytes()).decode()


def safe_in_script(text):
    # Keep inlined code from ending its <script> early or opening an HTML comment
    return re.sub(r"</(script)", r"<\\/\1", text, flags=re.I).replace("<!--", "<\\!--")


def minify_json(path):
    return json.dumps(json.loads((SRC / path).read_text(encoding="utf-8")),
                      separators=(",", ":"), ensure_ascii=False)


def main():
    html = (SRC / "index.html").read_text(encoding="utf-8")
    favicon = data_uri("assets/icons/favicon-64.png", "image/png")
    touch_icon = data_uri("assets/icons/apple-touch-icon.png", "image/png")

    # Head script: icons become data URIs; the manifest (needs separate files) is dropped
    html = html.replace('window.GN_ICON_URL = site("assets/icons/favicon-64.png");',
                        f'window.GN_ICON_URL = "{favicon}";')
    html = html.replace('add("apple-touch-icon", site("assets/icons/apple-touch-icon.png"));',
                        f'add("apple-touch-icon", "{touch_icon}");')
    html = html.replace('add("manifest", site("manifest.json"));', "")
    for needle in ('window.GN_ICON_URL = "data:', 'add("apple-touch-icon", "data:'):
        if needle not in html:
            sys.exit(f"build.py: couldn't rewrite the icon line ({needle}); index.html changed")

    # Stylesheet
    def inline_css(m):
        css = (SRC / m.group(1)).read_text(encoding="utf-8")
        return "<style>\n" + css.replace("</style", "<\\/style") + "\n</style>"
    html, n = re.subn(r'<link rel="stylesheet" href="([^"?]+)(?:\?[^"]*)?">', inline_css, html)
    if n == 0:
        sys.exit("build.py: no stylesheet found to inline")

    # Scripts
    seen = []
    def inline_js(m):
        path = m.group(1)
        seen.append(path)
        if path in SKIP_SCRIPTS:
            return f"<!-- {path} left out: service workers need a hosted multi-file site -->"
        js = (SRC / path).read_text(encoding="utf-8")
        return f"<script>/* {path} */\n{safe_in_script(js)}\n</script>"
    html = re.sub(r'<script src="([^"?]+)(?:\?[^"]*)?"></script>', inline_js, html)
    if not seen:
        sys.exit("build.py: no scripts found to inline")
    leftover = re.findall(r'<(?:script|link)[^>]+(?:src|href)="(?!https?:|data:)[^"]+"', html)
    if leftover:
        sys.exit(f"build.py: local files still referenced: {leftover}")

    # Config files, plus a fetch() wrapper that serves them from the page
    files = {p: minify_json(p) for p in EMBEDDED_FILES if (SRC / p).exists()}
    shim = """<script>
// Single-file build: the config files are inside this page, so fetches for
// them are answered here instead of going to the network.
(function () {
    var files = JSON.parse(document.getElementById("gn-embedded-files").textContent);
    var realFetch = window.fetch.bind(window);
    function key(input) {
        var u = typeof input === "string" ? input : (input && input.url) || "";
        if (/^[a-z][a-z0-9+.-]*:/i.test(u)) {
            // Absolute URL: only answer for this page's own location
            try {
                var abs = new URL(u), here = new URL(location.href);
                if (abs.origin !== here.origin) return null;
                var base = here.pathname.replace(/[^/]*$/, "");
                if (abs.pathname.indexOf(base) !== 0) return null;
                u = abs.pathname.slice(base.length);
            } catch (e) { return null; }
        }
        u = u.split(/[?#]/)[0].replace(/^\\.\\//, "");
        return Object.prototype.hasOwnProperty.call(files, u) ? u : null;
    }
    window.fetch = function (input, init) {
        var k = key(input);
        if (k) return Promise.resolve(new Response(files[k], { status: 200, headers: { "Content-Type": "application/json" } }));
        return realFetch(input, init);
    };
    window.GN_SINGLE_FILE = true;
})();
</script>"""
    embedded = ('<script type="application/json" id="gn-embedded-files">'
                + safe_in_script(json.dumps(files, separators=(",", ":"), ensure_ascii=False))
                + "</script>\n")
    # Must run before any site script, so put it right after <head>
    html = html.replace("<head>", "<head>\n" + embedded + shim, 1)

    commit = ""
    try:
        import subprocess
        commit = subprocess.run(["git", "-C", str(SRC), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        pass
    banner = ("<!-- GN 2.0 single-file build. Generated by build.py from SCHSwork/math"
              + (f" @ {commit}" if commit else "") + ". Don't edit by hand. -->\n")
    html = html.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + banner, 1)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB): "
          f"{len(seen) - len(SKIP_SCRIPTS & set(seen))} scripts, {len(files)} config files inlined")


if __name__ == "__main__":
    main()
