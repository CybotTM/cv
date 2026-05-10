#!/usr/bin/env python3
from pathlib import Path
import re, sys
html = Path(sys.argv[1]).read_text(encoding='utf-8')
out = Path(sys.argv[2])
text = re.sub('<[^<]+?>', ' ', html)
text = re.sub(r'\s+', ' ', text)[:120]
content = f"BT /F1 12 Tf 40 780 Td ({text.replace('(', '[').replace(')', ']')}) Tj ET".encode()
objs=[
b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
b"4 0 obj << /Length %d >> stream\n"%len(content)+content+b"\nendstream endobj\n",
b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"]
pdf=b"%PDF-1.4\n"; offs=[]
for o in objs: offs.append(len(pdf)); pdf+=o
xref=len(pdf)
pdf+=f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()+b''.join(f"{o:010d} 00000 n \n".encode() for o in offs)
pdf+=f"trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
out.write_bytes(pdf)
