#!/usr/bin/env python3
"""Build a single-file version of GN 2.0.

Reads a checkout of SCHSwork/math and writes one index.html with every CSS file,
JS file, config JSON and icon inlined. Nothing else is needed to run the site:
it can be opened straight from disk (file://), hosted anywhere, or shared as
one file.

It's a clean copy for other people to host with their own Firebase: no
Firebase project, owner settings or links to the original site's repos are
built in. Hosts fill in one GN_CONFIG block at the top of the file.

Usage:
    python3 build.py <path to SCHSwork/math checkout> [output file]
"""
import base64
import json
import re
import sys
from pathlib import Path

ARGS = [a for a in sys.argv[1:] if a != "--template"]
TEMPLATE = True   # always: this repo only ships the clean copy
SRC = Path(ARGS[0] if len(ARGS) > 0 else "math")
OUT = Path(ARGS[1] if len(ARGS) > 1 else "index.html")

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


# ── Template build ──────────────────────────────────────────────────────────
TEMPLATE_CONFIG = """<script>
// ═════════════════════════════════════════════════════════════════════════════
//  YOUR SETTINGS: the only part of this file you need to edit.
//  Step-by-step guide: SETUP.md, which comes with this file.
// ═════════════════════════════════════════════════════════════════════════════
window.GN_CONFIG = {
    // Accounts + cloud saves. Paste your Firebase web config here, e.g.
    //   firebase: { apiKey: "...", authDomain: "...", projectId: "...",
    //               storageBucket: "...", messagingSenderId: "...", appId: "..." },
    // Leave it null and the site works without accounts.
    firebase: null,

    // Optional: a GitHub repo of yours ("you/your-repo") holding
    // config/owner-settings.json, for the owner panel (lock the site,
    // announcements, disable games). Leave "" to turn that off.
    settingsRepo: ""
};
</script>
"""

CLEAN_OWNER_SETTINGS = {
    "siteMode": "open",
    "disabledZones": [],
    "announcement": {"text": "", "enabled": False, "type": "info"},
    "siteMessage": "",
    "statusOverride": {"level": "auto", "text": ""},
    "motd": {"text": "", "enabled": False},
    "footerLinks": [],
    "visitorDefaults": {
        "mode": "dark", "theme": "red", "cardSize": "medium", "fontSize": "medium",
        "defaultSort": "name", "compactMode": False, "hideFeatured": False,
        "autofocusSearch": True, "showPlayCount": True, "warnBeforeUnload": False,
        "reducedMotion": False
    },
    "trustedReporters": []
}


def patch(js, path, old, new, regex=False):
    out, n = (re.subn(old, new, js, count=1) if regex else (js.replace(old, new, 1), js.count(old)))
    if n == 0:
        sys.exit(f"build.py --template: couldn't find what to change in {path} ({old[:60]!r}); the site's code changed")
    return out


def template_js(path, js):
    if path == "js/accounts.js":
        # The real config is the first FIREBASE_CONFIG (the second one is an example in a comment)
        js = patch(js, path, r"const FIREBASE_CONFIG = \{[^}]*\};",
                   "const FIREBASE_CONFIG = (window.GN_CONFIG && window.GN_CONFIG.firebase) || null;", regex=True)
    if path == "js/app.js":
        guard = "\n    if (!(window.GN_CONFIG && window.GN_CONFIG.settingsRepo)) return {}; // template: no settings repo set\n"
        js = patch(js, path, 'const GITHUB_SYNC_REPO  = "SCHSwork/math";',
                   'const GITHUB_SYNC_REPO  = (window.GN_CONFIG && window.GN_CONFIG.settingsRepo) || "";')
        # Owner Panel stays locked until the host sets settingsRepo
        js = patch(js, path, "async function requestOwnerAccess(onSuccess) {",
                   "async function requestOwnerAccess(onSuccess) {\n"
                   "    if (!GITHUB_SYNC_REPO) { if (typeof notify === \"function\") notify(\"The Owner Panel isn't set up on this site (see SETUP.md, part E).\"); return; }")
        # Source health check: use the game library's own list instead of the original site's repo
        js = patch(js, path, 'MIRRORS[name]("SCHSwork", "math", "main", "config/library-pinned.json")',
                   'MIRRORS[name]("freebuisness", "assets", "main", "zones.json")')
        js = patch(js, path, "put it in SCHSwork/GN-originals (see its README), then mark it added.",
                   "add it to your site, then mark it added.")
        # Locked-down viewers (phone Files apps) can't reach into the game frame;
        # fill it with srcdoc there instead.
        for src in ("gameLoadingScreenHtml(file)", "html"):
            js = patch(js, path,
                       f"zoneFrame.contentDocument.open();\n            zoneFrame.contentDocument.write({src});\n            zoneFrame.contentDocument.close();"
                       if src == "html" else
                       f"zoneFrame.contentDocument.open();\n        zoneFrame.contentDocument.write({src});\n        zoneFrame.contentDocument.close();",
                       f"gnWriteFrame(zoneFrame, {src});")
        js = patch(js, path, "let zoneOpenToken = 0;",
                   "let zoneOpenToken = 0;\n"
                   "function gnWriteFrame(frame, html) {\n"
                   "    const doc = frame.contentDocument;\n"
                   "    if (doc) { doc.open(); doc.write(html); doc.close(); }\n"
                   "    else frame.srcdoc = html;\n"
                   "}")
        js = patch(js, path, "if (zoneFrame.contentDocument === null) replaceZoneFrame();", "")
        # Opened from disk, blob: URLs look like "blob:null/<id>". Older Unity
        # loaders only treat http/https/ftp/file URLs as absolute, so they glue
        # these onto the game's folder ("…/198/blob:null/<id>") and the last
        # download 404s: the game stops near the end of loading. Undo that inside
        # every game page.
        # (No backslashes in this snippet: it goes inside a JS template literal.)
        blob_fix = ('<script>(function(){var re=new RegExp("/(blob:null/[0-9a-f-]{36})([?#]|$)","i");'
                    'function fix(u){try{var s=String(u&&u.url!==undefined?u.url:u);if(s.indexOf("blob:")===0)return null;var m=s.match(re);if(m)return m[1]}catch(e){}return null}'
                    'var o=XMLHttpRequest.prototype.open;XMLHttpRequest.prototype.open=function(m,u){var f=fix(u);if(f){var a=[].slice.call(arguments);a[1]=f;return o.apply(this,a)}return o.apply(this,arguments)};'
                    'if(window.fetch){var F=window.fetch;window.fetch=function(i,n){var f=fix(i);return F.call(this,f||i,n)}}'
                    # Opened from disk, some engines (OpenFL/Lime: Run 3 etc.) assume every image is
                    # "same origin" and skip CORS, so WebGL refuses to draw them: black screen.
                    # Ask for CORS on images from hosts that allow it, only when opened from disk.
                    'if(self.origin==="null"){var H=new RegExp("^https?://(cdn[.]jsdelivr[.]net|raw[.]githubusercontent[.]com|rawcdn[.]githack[.]com|raw[.]githack[.]com|unpkg[.]com|[^/]+[.]github[.]io)/","i");'
                    'var d=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,"src");'
                    'if(d&&d.set)Object.defineProperty(HTMLImageElement.prototype,"src",{configurable:true,enumerable:d.enumerable,get:d.get,set:function(v){try{if(this.crossOrigin===null&&H.test(new URL(v,document.baseURI).href))this.crossOrigin="anonymous"}catch(e){}d.set.call(this,v)}});'
                    'var sa=Element.prototype.setAttribute;Element.prototype.setAttribute=function(n,v){try{if(this instanceof HTMLImageElement&&String(n).toLowerCase()==="src"&&this.crossOrigin===null&&H.test(new URL(v,document.baseURI).href))this.crossOrigin="anonymous"}catch(e){}return sa.apply(this,arguments)}}'
                    '})();</scr${""}ipt>')
        js = patch(js, path, "`})();<\\/script><style>#sidebarad1,#sidebarad2{display:none!important}</style>` +",
                   "`})();<\\/script><style>#sidebarad1,#sidebarad2{display:none!important}</style>` +\n        `" + blob_fix + "` +")
        js = patch(js, path, "async function githubSyncPull({ rerender = false } = {}) {",
                   "async function githubSyncPull({ rerender = false } = {}) {"
                   + guard.replace(" return {};", " return;"))
        js = patch(js, path, "async function githubSyncPushOnce() {",
                   "async function githubSyncPushOnce() {" + guard.replace(" return {};", " return false;"))
    if path == "js/library.js":
        # Changelog comes from the host's settings repo, if they have one
        js = patch(js, path, "async function loadChangelog() {",
                   "async function loadChangelog() {\n"
                   "    if (!GITHUB_SYNC_REPO) { legalPopup(\"Changelog\", \"<p>This site doesn't have a changelog.</p>\"); return; }")
    return js


STORAGE_SHIM = """<script>
// Phone file viewers (opening the file from Files / Downloads) often block
// browser storage, and reading it throws. The site reads storage as it starts,
// so without this it would stop at "Loading games…". Fall back to in-memory
// storage: everything works, but settings and favorites last only until the
// page is closed.
(function () {
    function memoryStorage() {
        var data = {};
        var api = {
            getItem: function (k) { k = String(k); return Object.prototype.hasOwnProperty.call(data, k) ? data[k] : null; },
            setItem: function (k, v) { data[String(k)] = String(v); },
            removeItem: function (k) { delete data[String(k)]; },
            clear: function () { data = {}; },
            key: function (i) { var ks = Object.keys(data); return i < ks.length ? ks[i] : null; }
        };
        Object.defineProperty(api, "length", { get: function () { return Object.keys(data).length; } });
        return api;
    }
    var blocked = [];
    ["localStorage", "sessionStorage"].forEach(function (name) {
        try {
            var s = window[name];
            var t = "__gn_test__";
            s.setItem(t, "1"); s.removeItem(t);
        } catch (e) {
            try {
                Object.defineProperty(window, name, { value: memoryStorage(), configurable: true });
                blocked.push(name);
            } catch (e2) {}
        }
    });
    try { void document.cookie; } catch (e) {
        try { Object.defineProperty(document, "cookie", { get: function () { return ""; }, set: function () {}, configurable: true }); } catch (e2) {}
    }
    window.GN_STORAGE_BLOCKED = blocked.length > 0;
    if (window.GN_STORAGE_BLOCKED) {
        window.addEventListener("load", function () {
            setTimeout(function () {
                var msg = "This app can't save, so favorites, settings and game progress reset when you close it. For saves, open the file in Chrome or another browser.";
                if (typeof notify === "function") notify(msg); else console.warn(msg);
            }, 2500);
        });
    }
})();
</script>
"""

NOSCRIPT = """<noscript><div style="position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;padding:24px;background:#0f172a;color:#f1f5f9;font:16px/1.5 system-ui,sans-serif;text-align:center;">
<div><h2 style="margin:0 0 12px;">This app can't run games</h2>
<p style="margin:0;">The viewer you opened this file with has JavaScript turned off. Open the file in a web browser instead, like Chrome, Edge, Firefox or Safari.</p></div></div></noscript>
"""


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

    if TEMPLATE:
        gn_light = '<a href="https://schswork.github.io/gn-light/" title="A faster, simpler version for slow computers">GN Light</a>'
        if gn_light not in html:
            sys.exit("build.py: couldn't find the GN Light footer link; index.html changed")
        html = html.replace(gn_light, "")

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
        if TEMPLATE:
            js = template_js(path, js)
        return f"<script>/* {path} */\n{safe_in_script(js)}\n</script>"
    html = re.sub(r'<script src="([^"?]+)(?:\?[^"]*)?"></script>', inline_js, html)
    if not seen:
        sys.exit("build.py: no scripts found to inline")
    leftover = re.findall(r'<(?:script|link)[^>]+(?:src|href)="(?!https?:|data:)[^"]+"', html)
    if leftover:
        sys.exit(f"build.py: local files still referenced: {leftover}")

    # Config files, plus a fetch() wrapper that serves them from the page
    files = {p: minify_json(p) for p in EMBEDDED_FILES if (SRC / p).exists()}
    if TEMPLATE:
        files["config/owner-settings.json"] = json.dumps(CLEAN_OWNER_SETTINGS, separators=(",", ":"))
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
    html = html.replace("<head>", "<head>\n" + STORAGE_SHIM + (TEMPLATE_CONFIG if TEMPLATE else "") + embedded + shim, 1)
    html = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + NOSCRIPT, html, count=1)

    commit = ""
    try:
        import subprocess
        commit = subprocess.run(["git", "-C", str(SRC), "rev-parse", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        pass
    banner = ("<!-- GN 2.0 single-file site. Fill in GN_CONFIG below; see SETUP.md."
              + (f" Built from GN 2.0 @ {commit[:10]}." if commit else "") + " -->\n")
    html = html.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + banner, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    if TEMPLATE and (SRC / "config/firestore.rules").exists():
        (OUT.parent / "firestore.rules").write_text((SRC / "config/firestore.rules").read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB): "
          f"{len(seen) - len(SKIP_SCRIPTS & set(seen))} scripts, {len(files)} config files inlined")


if __name__ == "__main__":
    main()
