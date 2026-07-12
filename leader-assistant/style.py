"""CSS and JS for the Leader Assistant UI."""

CSS = """
:root {
  --blue: #209dd7;
  --ink: #1b1f24;
  --muted: #828a94;
  --line: #e7e9ee;
  --panel: #ffffff;
  --bg: #f4f5f7;
}

.dark {
  color-scheme: light !important;
  --body-background-fill: #f4f5f7 !important;
  --background-fill-primary: #ffffff !important;
  --background-fill-secondary: #f4f5f7 !important;
  --block-background-fill: #ffffff !important;
  --panel-background-fill: #ffffff !important;
  --body-text-color: #1b1f24 !important;
  --border-color-primary: #e7e9ee !important;
}

html, body, gradio-app { background: var(--bg) !important; color-scheme: light; }
.gradio-container { background: var(--bg) !important; max-width: 900px !important; margin: 0 auto !important; }
.gradio-container, .gradio-container * {
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
footer { display: none !important; }

#app_title { font-weight: 750; font-size: 1.4rem; letter-spacing: -0.02em; margin: 4px 2px 12px; color: var(--ink); }
#app_title b { color: var(--blue); font-weight: 750; }

#chat { border: 1px solid var(--line) !important; border-radius: 12px !important; background: var(--panel) !important; }
#chat .message.user, #chat .user { background: rgba(32,157,215,.10) !important; border: 0 !important; }
#chat .message.bot, #chat .bot { background: #f3f4f6 !important; border: 0 !important; }
#msgbox textarea { border-radius: 10px !important; border: 1px solid var(--line) !important; background: var(--panel) !important; }
#msgbox textarea:focus { border-color: var(--blue) !important; box-shadow: 0 0 0 3px rgba(32,157,215,.14) !important; }

.thinking { display:inline-flex; gap:5px; align-items:center; padding: 2px 0; }
.thinking i { width:7px; height:7px; border-radius:50%; background: var(--blue); display:inline-block; animation: blink 1.2s infinite ease-in-out; }
.thinking i:nth-child(2) { animation-delay:.18s; }
.thinking i:nth-child(3) { animation-delay:.36s; }
@keyframes blink { 0%,80%,100%{opacity:.25; transform:translateY(0)} 40%{opacity:1; transform:translateY(-3px)} }
"""

HEAD = """
<script>
(function () {
  var u = new URL(window.location.href);
  if (u.searchParams.get('__theme') !== 'light') {
    u.searchParams.set('__theme', 'light');
    window.location.replace(u.href);
    return;
  }
  var iv = setInterval(function () {
    var ta = document.querySelector('#msgbox textarea');
    if (ta) { ta.focus(); clearInterval(iv); }
  }, 250);
})();
</script>
"""
