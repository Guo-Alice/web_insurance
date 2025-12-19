#!/usr/bin/env python3
"""
创建默认favicon.ico文件
"""
import os
import base64

# 最简单的16x16像素ICO文件（白色透明）
FAVICON_DATA = base64.b64decode("""
AAABAAEAEBAQAAEABAAoAQAAFgAAACgAAAAQAAAAIAAAAAEABAAAAAAAgAAAAAAAAAAAAAAAEAAA
AAAAAACAAACAAAAAAIAAAIAAAAAAAAAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//
AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA
""")

# 写入文件
static_dir = os.path.join(os.path.dirname(__file__), 'static')
favicon_path = os.path.join(static_dir, 'favicon.ico')

os.makedirs(static_dir, exist_ok=True)

with open(favicon_path, 'wb') as f:
    f.write(FAVICON_DATA)

print(f"✅ 已创建默认favicon.ico: {favicon_path}")
