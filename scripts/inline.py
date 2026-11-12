"""Build a single-file copy (for quick previews): python scripts/inline.py > single.html"""
import os, re
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
r = lambda f: open(os.path.join(d, f), encoding='utf-8').read()
s = r('index.html')
s = re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n?', '', s)
s = re.sub(r'<link rel="(manifest|icon|apple-touch-icon)"[^>]*>\n?', '', s)
s = s.replace('<script src="config.js"></script>\n', '')
s = s.replace('<link rel="stylesheet" href="styles.css">', '<style>\n' + r('styles.css') + '</style>')
s = s.replace('<script src="app.js"></script>', '<script>\n' + r('app.js') + '</script>')
print(s)
