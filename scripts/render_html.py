#!/usr/bin/env python3
from pathlib import Path
import html, re, sys

def inline(md: str) -> str:
    txt = html.escape(md)
    txt = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', txt)
    txt = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', txt)
    return txt

src = Path(sys.argv[1])
out = Path(sys.argv[2])
css_href = sys.argv[3]
lines = src.read_text(encoding='utf-8').splitlines()
body=[]
in_list=False
for line in lines:
    s=line.strip()
    if not s:
        if in_list:
            body.append('</ul>'); in_list=False
        continue
    if s.startswith('# '):
        if in_list: body.append('</ul>'); in_list=False
        body.append(f"<h1>{inline(s[2:])}</h1>")
    elif s.startswith('## '):
        if in_list: body.append('</ul>'); in_list=False
        body.append(f"<h2>{inline(s[3:])}</h2>")
    elif s.startswith('### '):
        if in_list: body.append('</ul>'); in_list=False
        body.append(f"<h3>{inline(s[4:])}</h3>")
    elif s.startswith('- '):
        if not in_list:
            body.append('<ul>'); in_list=True
        body.append(f"<li>{inline(s[2:])}</li>")
    elif s == '---':
        if in_list: body.append('</ul>'); in_list=False
        body.append('<hr/>')
    else:
        if in_list: body.append('</ul>'); in_list=False
        body.append(f"<p>{inline(s)}</p>")
if in_list: body.append('</ul>')
out.write_text(f"<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/><link rel='stylesheet' href='{css_href}'/></head><body>\n"+'\n'.join(body)+"\n</body></html>\n", encoding='utf-8')
