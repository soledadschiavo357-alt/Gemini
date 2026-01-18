import urllib.request
import json
import os

# 配置信息
HOST = "gemini-vip.top"
KEY = "b571b53d075d4ba09bc1fc37b9e1da48"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
API_URL = "https://api.indexnow.org/indexnow"

def get_all_urls():
    """扫描当前目录，生成所有需要提交的 URL"""
    urls = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 扫描根目录 HTML
    for file in os.listdir(base_dir):
        if file.endswith(".html") and file not in ["404.html", "design.html", "layout_template.html"]:
            if file == "index.html":
                urls.append(f"https://{HOST}/")
            else:
                # Clean URL: remove .html
                clean_file = file.replace(".html", "")
                urls.append(f"https://{HOST}/{clean_file}")
    
    # 2. 扫描 blog 目录
    blog_dir = os.path.join(base_dir, "blog")
    if os.path.exists(blog_dir):
        for file in os.listdir(blog_dir):
            if file.endswith(".html"):
                # Clean URL: remove .html
                clean_file = file.replace(".html", "")
                if clean_file == "index":
                    urls.append(f"https://{HOST}/blog/")
                else:
                    urls.append(f"https://{HOST}/blog/{clean_file}")
    
    return urls

def push_to_bing(url_list):
    """提交 URL 到 Bing IndexNow"""
    data = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": url_list
    }
    
    json_data = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(
        API_URL, 
        data=json_data, 
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    
    print(f"正在提交 {len(url_list)} 个链接到 Bing IndexNow...")
    for url in url_list:
        print(f" - {url}")
        
    try:
        with urllib.request.urlopen(req) as response:
            code = response.getcode()
            if code == 200:
                print("\n✅ 提交成功！Bing 已经收到您的收录请求。")
            else:
                print(f"\n⚠️ 提交可能有问题，返回状态码: {code}")
                print(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"\n❌ 提交失败: {e.code} {e.reason}")
        print(e.read().decode("utf-8"))
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    urls = get_all_urls()
    if urls:
        push_to_bing(urls)
    else:
        print("未找到任何 HTML 文件。")
