import os
import re
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

BLOG_DIR = 'blog'
DOMAIN = "https://gemini-vip.top"
SITEMAP_XML = 'sitemap.xml'
POSTS_JSON = 'posts.json'

h1_pattern = re.compile(r'<h1[^>]*>(.*?)</h1>', re.DOTALL)
tag_pattern = re.compile(r'<[^>]+>')
date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')

def main():
    posts = []
    if not os.path.exists(BLOG_DIR):
        print("Blog dir not found")
        return

    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.html') and filename != 'index.html':
            filepath = os.path.join(BLOG_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            match = h1_pattern.search(content)
            title = "Untitled"
            if match:
                clean_title = tag_pattern.sub('', match.group(1))
                title = ' '.join(clean_title.split())
            
            date_match = date_pattern.search(content)
            date_str = date_match.group(1) if date_match else datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d')
            
            slug = filename[:-5]
            url = f"{DOMAIN}/blog/{slug}"
            
            posts.append({'title': title, 'url': url, 'date': date_str})
    
    posts.sort(key=lambda x: x['date'], reverse=True)
    
    # JSON
    with open(POSTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
        
    # XML
    urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    static_pages = [
        {'loc': f'{DOMAIN}/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': f'{DOMAIN}/about', 'priority': '0.6', 'changefreq': 'monthly'},
        {'loc': f'{DOMAIN}/legal', 'priority': '0.5', 'changefreq': 'monthly'},
        {'loc': f'{DOMAIN}/blog/', 'priority': '0.9', 'changefreq': 'daily'},
        {'loc': f'{DOMAIN}/sitemap', 'priority': '0.4', 'changefreq': 'weekly'},
    ]
    for page in static_pages:
        u = ET.SubElement(urlset, 'url')
        ET.SubElement(u, 'loc').text = page['loc']
        ET.SubElement(u, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
        ET.SubElement(u, 'priority').text = page['priority']
        ET.SubElement(u, 'changefreq').text = page['changefreq']
        
    for post in posts:
        u = ET.SubElement(urlset, 'url')
        ET.SubElement(u, 'loc').text = post['url']
        ET.SubElement(u, 'lastmod').text = post['date']
        ET.SubElement(u, 'priority').text = '0.8'
        ET.SubElement(u, 'changefreq').text = 'weekly'
        
    xml_str = minidom.parseString(ET.tostring(urlset)).toprettyxml(indent="  ")
    # remove the xml version line added by minidom if you want strict control, but usually it's fine.
    # ET adds <?xml ... ?> if we use ElementTree.write, but minidom toprettyxml adds it too.
    # Let's write it.
    with open(SITEMAP_XML, 'w', encoding='utf-8') as f:
        f.write(xml_str)

    # HTML Snippet Output
    print("--- HTML SNIPPET START ---")
    for post in posts:
        rel_url = post['url'].replace(DOMAIN, '')
        print(f'''            <li>
              <a href="{rel_url}" class="flex items-start gap-3 text-slate-400 hover:text-white transition group hover-arrow">
                <i class="fa-solid fa-file-lines mt-1 text-xs text-slate-600 group-hover:text-pink-400 transition"></i>
                <div>
                  <span class="block text-sm font-medium group-hover:underline decoration-pink-500/50 underline-offset-4 decoration-1 transition">{post['title']}</span>
                  <span class="text-[10px] text-slate-600 font-mono">{post['date']}</span>
                </div>
              </a>
            </li>''')
    print("--- HTML SNIPPET END ---")

if __name__ == "__main__":
    main()
