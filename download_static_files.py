import os
import requests

# 创建目录
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/fonts', exist_ok=True)

# 要下载的文件列表
files_to_download = [
    {
        'url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
        'path': 'static/css/bootstrap.min.css'
    },
    {
        'url': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css',
        'path': 'static/css/bootstrap-icons.css'
    },
    {
        'url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js',
        'path': 'static/js/bootstrap.bundle.min.js'
    },
    {
        'url': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/fonts/bootstrap-icons.woff2',
        'path': 'static/fonts/bootstrap-icons.woff2'
    },
    {
        'url': 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/fonts/bootstrap-icons.woff',
        'path': 'static/fonts/bootstrap-icons.woff'
    }
]

print("开始下载静态资源文件...")
for file_info in files_to_download:
    url = file_info['url']
    path = file_info['path']
    
    try:
        print(f"正在下载: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        with open(path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 已保存到: {path}")
    except Exception as e:
        print(f"❌ 下载失败 {url}: {e}")

print("\n下载完成！")
