import urllib.request
import os

# 配置信息
API_URL = "http://data.zz.baidu.com/urls?site=https://gemini-vip.top&token=MkpV4it8Aq1PaVbS"
HOST = "gemini-vip.top"
MAX_PUSH_COUNT = 9  # 每天剩余配额预估，保守设置为 9

def get_priority_urls():
    """获取优先级最高的 URL，避免超出配额"""
    urls = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 必推：核心页面
    priority_pages = ["legal.html", "index.html"]
    for page in priority_pages:
        if page == "index.html":
            urls.append(f"https://{HOST}/")
        else:
            # Clean URL: remove .html
            clean_page = page.replace(".html", "")
            urls.append(f"https://{HOST}/{clean_page}")
            
    # 2. 选推：Blog 页面 (按修改时间排序，推最新的)
    blog_dir = os.path.join(base_dir, "blog")
    blog_urls = []
    if os.path.exists(blog_dir):
        files = []
        for file in os.listdir(blog_dir):
            if file.endswith(".html"):
                full_path = os.path.join(blog_dir, file)
                files.append((full_path, file))
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
        
        for _, file in files:
            if file == "index.html":
                blog_urls.append(f"https://{HOST}/blog/")
            else:
                # Clean URL: remove .html
                clean_file = file.replace(".html", "")
                blog_urls.append(f"https://{HOST}/blog/{clean_file}")

    # 合并列表
    urls.extend(blog_urls)
    
    # 3. 截断列表，防止超额
    final_list = urls[:MAX_PUSH_COUNT]
    
    # 打印被舍弃的链接，方便查看
    if len(urls) > MAX_PUSH_COUNT:
        print(f"⚠️ 注意：共有 {len(urls)} 个链接，但为了不超配额，只推送前 {MAX_PUSH_COUNT} 个。")
        print("被暂时忽略的链接：")
        for ignored in urls[MAX_PUSH_COUNT:]:
            print(f" - {ignored}")
            
    return final_list

def push_to_baidu(url_list):
    """提交 URL 到 百度站长平台"""
    if not url_list:
        print("没有需要推送的链接。")
        return

    data = "\n".join(url_list).encode("utf-8")
    
    headers = {
        'User-Agent': 'curl/7.12.1',
        'Content-Type': 'text/plain'
    }
    
    req = urllib.request.Request(
        API_URL, 
        data=data, 
        headers=headers
    )
    
    print(f"\n🚀 正在向百度推送 {len(url_list)} 个核心链接...")
    for url in url_list:
        print(f" - {url}")
        
    try:
        with urllib.request.urlopen(req) as response:
            code = response.getcode()
            result = response.read().decode("utf-8")
            print(f"\n【百度返回结果】: {result}")
            
            if code == 200 and "success" in result:
                print("✅ 推送成功！")
            else:
                print(f"⚠️ 推送可能存在问题，状态码: {code}")
                
    except urllib.error.HTTPError as e:
        print(f"\n❌ 提交失败: {e.code} {e.reason}")
        print(e.read().decode("utf-8"))
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    urls = get_priority_urls()
    if urls:
        push_to_baidu(urls)
