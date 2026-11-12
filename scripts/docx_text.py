#!/usr/bin/env python3
"""Print the text of a .docx file, one paragraph per line. Table cells are separated by " | ".
Standard library only.   Usage: python3 docx_text.py file.docx"""
import html
import re
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as z:
    xml = z.read("word/document.xml").decode("utf-8", "ignore")
xml = xml.replace("</w:tc>", "<w:t> | </w:t>").replace("<w:tab/>", "<w:t>\t</w:t>").replace("</w:tr>", "</w:p>")
for para in xml.split("</w:p>"):
    text = html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", para))).strip(" |")
    if text.strip():
        print(text.strip())
