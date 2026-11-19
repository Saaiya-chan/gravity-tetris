#!/usr/bin/env python3
"""ゲームで使う文字だけを M PLUS Rounded 1c ExtraBold から切り出して、free.html に埋め込む。
文言を変えたら実行する:  python3 tools/subset_font.py /path/to/MPLUSRounded1c-ExtraBold.ttf
フォント: M PLUS Rounded 1c (SIL Open Font License 1.1) https://fonts.google.com/specimen/M+PLUS+Rounded+1c
"""
import sys, re, base64, io
from fontTools import subset
from fontTools.ttLib import TTFont
src = sys.argv[1]; html_path = sys.argv[2] if len(sys.argv) > 2 else "free.html"
html = open(html_path, encoding="utf-8").read()
body = re.sub(r"/\*FONT64\*/.*?/\*END64\*/", "", html, flags=re.S)
chars = set(body) | set(map(chr, range(0x20, 0x7f))) | set(map(chr, range(0x3041, 0x3097))) | set(map(chr, range(0x30a1, 0x30fd)))
chars |= set("、。・「」（）！？ー〜…：％＋－×÷＝→←↑↓¥￥々〇０１２３４５６７８９年月日時分秒円個回点位人目中上下左右大小")
opts = subset.Options(); opts.layout_features = ["*"]; opts.flavor = "woff"; opts.with_zopfli = False; opts.name_IDs = [1, 2]; opts.notdef_outline = True
font = TTFont(src); sub = subset.Subsetter(opts); sub.populate(text="".join(sorted(chars))); sub.subset(font)
buf = io.BytesIO(); font.flavor = "woff"; font.save(buf); b64 = base64.b64encode(buf.getvalue()).decode()
new = re.sub(r"/\*FONT64\*/.*?/\*END64\*/", lambda m: "/*FONT64*/" + b64 + "/*END64*/", html, flags=re.S)
assert new != html or b64 in html, "free.html に /*FONT64*/…/*END64*/ の目印がありません"
open(html_path, "w", encoding="utf-8").write(new)
print(f"{len(chars)} 文字, woff {len(buf.getvalue())//1024} KB")
