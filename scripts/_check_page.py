import urllib.request, re

html = urllib.request.urlopen('http://127.0.0.1:8000/project/7').read().decode('utf-8')
scripts = list(re.finditer(r'<script[^>]*>(.*?)</script>', html, re.DOTALL))
for i, m in enumerate(scripts):
    s = m.group(1)
    if 'createApp' in s or len(s) > 5000:
        opens = s.count('{')
        closes = s.count('}')
        ok = "OK" if opens == closes else "BROKEN"
        print("Script #%d: len=%d braces: {%d/%d} %s" % (i, len(s), opens, closes, ok))
        if 'function initColumnResize' in s:
            print("  -> initColumnResize defined HERE (inline)")
        if 'function syncDfmeaScrollbar' in s:
            print("  -> syncDfmeaScrollbar defined HERE (inline)")
        if 'detectParsed' in s:
            print("  -> detectParsed referenced")
