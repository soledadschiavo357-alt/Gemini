import os
import re
import json
import random
import update_sitemap
from bs4 import BeautifulSoup

TEMPLATE_FILE = 'layout_template.html'
BLOG_DIR = 'blog'

# Configuration Maps
SHADOW_MAP = {
    'purple': '168,85,247',
    'emerald': '16,185,129',
    'red': '239,68,68',
    'blue': '59,130,246',
    'green': '34,197,94',
    'pink': '236,72,153',
    'yellow': '234,179,8',
    'orange': '249,115,22',
    'cyan': '8,145,178',
    'slate': '148,163,184'
}

GRADIENT_MAP = {
    'purple': 'pink',
    'emerald': 'blue',
    'red': 'orange',
    'blue': 'purple',
    'green': 'emerald',
    'pink': 'purple',
    'yellow': 'orange',
    'cyan': 'blue',
    'orange': 'red',
    'slate': 'gray'
}

DEFAULT_THEMES = list(SHADOW_MAP.keys())
DEFAULT_ICONS = ['fa-robot', 'fa-star', 'fa-bolt', 'fa-book', 'fa-layer-group', 'fa-wand-magic-sparkles']

# Centralized Post Configuration for Consistency
POST_CONFIG = {
    'gemini-student-discount': {'color': 'emerald', 'icon': 'fa-graduation-cap', 'category': '教育优惠'},
    'is-gemini-worth-it': {'color': 'cyan', 'icon': 'fa-scale-balanced', 'category': '深度评测'},
    'gemini-pro-prompts': {'color': 'purple', 'icon': 'fa-wand-magic-sparkles', 'category': 'Prompt教程'},
    'gemini-version-guide': {'color': 'blue', 'icon': 'fa-code-branch', 'category': '版本指南'},
    'gemini-membership-guide': {'color': 'orange', 'icon': 'fa-gem', 'category': '会员攻略'},
    'how-to-use-gemini-3': {'color': 'indigo', 'icon': 'fa-book-open', 'category': '新手教程'},
    'gemini-veo-video-review': {'color': 'pink', 'icon': 'fa-video', 'category': '视频生成'},
    'benefits': {'color': 'red', 'icon': 'fa-gift', 'category': '会员权益'},
    'gemini-region-error-fix': {'color': 'slate', 'icon': 'fa-wrench', 'category': '故障排除'},
    'guide-cn': {'color': 'teal', 'icon': 'fa-language', 'category': '中文指南'},
    'choose-model-cn': {'color': 'violet', 'icon': 'fa-robot', 'category': '模型选型'},
    'comparison': {'color': 'yellow', 'icon': 'fa-not-equal', 'category': '竞品对比'},
    'pro-vs-free': {'color': 'green', 'icon': 'fa-circle-half-stroke', 'category': '版本对比'}
}

def get_template():
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def get_post_metadata(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Title
    title_match = re.search(r'<title>(.*?)</title>', content)
    title = title_match.group(1).split(' - ')[0] if title_match else 'No Title'
    
    # URL (Clean URL)
    filename = os.path.basename(filepath)
    url = filename.replace('.html', '')
    
    # Tags
    tags = []
    kw_match = re.search(r'<meta.*name="keywords".*content="([^"]*)".*>', content)
    if not kw_match:
        kw_match = re.search(r'<meta.*content="([^"]*)".*name="keywords".*>', content)
    
    if kw_match:
        tags = [t.strip() for t in kw_match.group(1).split(',')]
        
    # Date
    date_match = re.search(r'<time datetime="([^"]*)">', content)
    date = date_match.group(1) if date_match else '1970-01-01'
    
    # Content Length for Read Time
    main_text = ''
    main_match = re.search(r'<main.*?>(.*?)</main>', content, re.DOTALL)
    if main_match:
        main_text = re.sub(r'<[^>]+>', '', main_match.group(1))
    else:
        main_text = re.sub(r'<[^>]+>', '', content)
        
    text_length = len(main_text.strip())
    read_time = f"{max(1, text_length // 400)}分钟阅读"

    # Meta tags for Homepage Card
    # <meta name="card-icon" content="...">
    card_icon_match = re.search(r'<meta.*name="card-icon".*content="([^"]*)".*>', content)
    card_icon = card_icon_match.group(1) if card_icon_match else 'fa-star'
    
    # <meta name="card-color" content="...">
    card_color_match = re.search(r'<meta.*name="card-color".*content="([^"]*)".*>', content)
    card_color = card_color_match.group(1) if card_color_match else 'purple'
    
    # <meta name="card-category" content="...">
    card_category_match = re.search(r'<meta.*name="card-category".*content="([^"]*)".*>', content)
    card_category = card_category_match.group(1) if card_category_match else '教程'
    
    # <meta name="card-sticky" content="0">
    card_sticky_match = re.search(r'<meta.*name="card-sticky".*content="([^"]*)".*>', content)
    card_sticky = int(card_sticky_match.group(1)) if card_sticky_match and card_sticky_match.group(1).isdigit() else 0

    # Override with Central Config if available
    if url in POST_CONFIG:
        config = POST_CONFIG[url]
        card_color = config.get('color', card_color)
        card_icon = config.get('icon', card_icon)
        card_category = config.get('category', card_category)

    # Extract Summary from description meta or p tag
    summary = ''
    desc_match = re.search(r'<meta.*name="description".*content="([^"]*)".*>', content)
    if not desc_match:
        desc_match = re.search(r'<meta.*content="([^"]*)".*name="description".*>', content)
    if desc_match:
        summary = desc_match.group(1)
    
    return {
        'title': title,
        'url': url,
        'tags': tags,
        'date': date,
        'read_time': read_time,
        'filepath': filepath,
        'card_icon': card_icon,
        'card_color': card_color,
        'card_category': card_category,
        'card_sticky': card_sticky,
        'summary': summary
    }

def get_related_posts(current_post, all_posts):
    # Filter out current post
    candidates = [p for p in all_posts if p['url'] != current_post['url']]
    
    scored_candidates = []
    current_tags = set(current_post['tags'])
    
    for p in candidates:
        other_tags = set(p['tags'])
        overlap = len(current_tags.intersection(other_tags))
        scored_candidates.append({
            'post': p,
            'overlap': overlap
        })
    
    # Sort by overlap (desc), then date (desc)
    scored_candidates.sort(key=lambda x: x['post']['date'], reverse=True)
    scored_candidates.sort(key=lambda x: x['overlap'], reverse=True)
    
    # Return top 4 posts
    return [x['post'] for x in scored_candidates[:4]]

def generate_related_posts_html(related_posts, style_db):
    if not related_posts:
        return ''
        
    html = '<div class="mt-16 border-t border-white/10 pt-10">\n'
    html += '  <h3 class="text-xl font-bold text-white mb-6">相关文章推荐</h3>\n'
    html += '  <div class="grid grid-cols-1 md:grid-cols-4 gap-6">\n'
    
    for post in related_posts:
        url = post['url']
        
        # Get Style from Metadata or Config
        color = post.get('card_color', 'purple')
        icon = post.get('card_icon', 'fa-star')
        category = post.get('card_category', '推荐文章')
        
        # Fallback if coming from old style_db
        if url in style_db:
            s = style_db[url]
            color = s.get('color', color)
            icon = s.get('icon', icon)
            category = s.get('category', category)
        
        # Derived values
        secondary_color = GRADIENT_MAP.get(color, 'purple')
        
        # HTML Template (Small Card Style - as requested)
        card_html = f'''
    <a class="group block rounded-2xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition" href="{url}">
      <div class="h-28 rounded-xl bg-gradient-to-br from-{color}-600/20 to-{secondary_color}-600/20 flex items-center justify-center text-{color}-400 mb-3">
        <i class="fa-solid {icon} text-3xl"></i>
      </div>
      <div class="text-white font-bold text-sm line-clamp-2">{post['title']}</div>
      <div class="text-slate-500 text-xs mt-1">{category}</div>
    </a>
'''
        html += card_html
        
    html += '  </div>\n'
    html += '</div>'
    return html

def sanitize_links(html_content):
    def replace_relative_index(match):
        anchor = match.group(1) or ''
        return f'href="/{anchor}"'
    
    html_content = re.sub(r'href="(?:\.\./)+index\.html(#[^"]*)?"', replace_relative_index, html_content)
    html_content = re.sub(r'href="(?:\.\./)+index(#[^"]*)?"', replace_relative_index, html_content)

    def remove_html_ext(match):
        url = match.group(1)
        if url.startswith(('http:', 'https:', 'mailto:', 'tel:', '//', '#')):
            return match.group(0)
        return f'href="{url}"'

    html_content = re.sub(r'href="([^"]+)\.html"', remove_html_ext, html_content)
    
    def resolve_parent_refs(match):
        path = match.group(1)
        return f'href="/{path}"'
        
    html_content = re.sub(r'href="\.\./([^"]+)"', resolve_parent_refs, html_content)
    
    def fix_canonical(match):
        url = match.group(1)
        return f'<link href="{url}" rel="canonical"/>'
    
    html_content = re.sub(r'<link href="([^"]+)\.html" rel="canonical"/>', fix_canonical, html_content)
    
    return html_content

def update_indices():
    print("Updating indices...")
    update_sitemap.main()

def process_file(filepath, template_content, all_posts):
    print(f"Processing file: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return
    
    match = re.search(r'(<main.*?>.*?</main>)', content, re.DOTALL)
    if match:
        print(f"DEBUG: Found <main> in {filepath}")
    else:
        print(f"Warning: No <main> tag found in {filepath}. Skipping content injection.")
        return
    
    # Use BS to clean up the main content first
    try:
        main_content_raw = match.group(1)
        soup = BeautifulSoup(main_content_raw, 'html.parser')
        print(f"DEBUG: Soup parsed for {filepath}")
    except Exception as e:
        print(f"Error parsing soup for {filepath}: {e}")
        return
    
    # --- Remove Category Badge ---
    # Find the header inside article
    article = soup.find('article')
    if article:
        header = article.find('header')
        if header:
            # Look for the badge div: div.inline-block.px-3.py-1.rounded-full...
            badge = header.find('div', class_=lambda c: c and 'inline-block' in c and 'px-3' in c and 'rounded-full' in c)
            if badge:
                badge.decompose()
            
            # --- Ensure Inner Breadcrumb Exists (Restore if missing) ---
            inner_breadcrumb = header.find('nav', attrs={'aria-label': 'Breadcrumb'})
            if not inner_breadcrumb:
                # Restore the inner breadcrumb
                current_post = next((p for p in all_posts if p['filepath'] == filepath), None)
                post_title = current_post['title'] if current_post else '文章详情'
                
                # Using the exact same structure as the reference code (指令.md)
                # Added mt-12 to compensate for the removed Category Badge and ensure breathing room.
                inner_bc_html = f'''
                <nav aria-label="Breadcrumb" class="overflow-x-auto whitespace-nowrap mb-6 mt-12">
                <ol class="flex items-center gap-2 text-sm text-slate-400">
                <li><a class="hover:text-white transition" href="/">首页</a></li>
                <li><span class="mx-1">/</span></li>
                <li><a class="hover:text-white transition" href="/blog/">教程资源</a></li>
                <li><span class="mx-1">/</span></li>
                <li aria-current="page" class="text-white font-medium">{post_title}</li>
                </ol>
                </nav>
                '''
                header.insert(0, BeautifulSoup(inner_bc_html, 'html.parser'))
            else:
                # If it exists, ensure it matches the reference style (reset classes)
                # Remove all styling hacks we added previously, add mt-12
                inner_breadcrumb['class'] = ['overflow-x-auto', 'whitespace-nowrap', 'mb-6', 'mt-12']
                
                # Ensure the ol inside has the correct classes
                ol = inner_breadcrumb.find('ol')
                if ol:
                    ol['class'] = ['flex', 'items-center', 'gap-2', 'text-sm', 'text-slate-400']
                    
                    # Update the "Tutorial Resources" link href to /blog/
                    for a in ol.find_all('a'):
                        if 'href' in a.attrs and ('blog' in a['href'] or '教程' in a.get_text()):
                            a['href'] = '/blog/'
                    
                    # Ensure the active item (last li) has correct style
                    last_li = ol.find_all('li')[-1]
                    if last_li:
                        last_li['class'] = ['text-white', 'font-medium']
                        if last_li.has_attr('aria-current'):
                             pass # keep it
                        else:
                             last_li['aria-current'] = 'page'
                
    # --- Aggressive Cleanup (The Cleaner) ---
    # Strategy: Keep the main content wrapper, remove everything else in <main>.
    # This removes old breadcrumbs (if any inside main), old related posts, and any garbage text nodes.
    
    main_wrapper = soup.find('div', class_='grid grid-cols-1 lg:grid-cols-3 gap-12')
    main_tag = soup.find('main')
    
    if main_wrapper and main_tag:
        # Deep Clean: Wipe main and restore only the content wrapper
        main_tag.clear()
        main_tag.append(main_wrapper)
    else:
        # Fallback: if structure is different (e.g. no sidebar), use the specific element removal method
        # Find all divs that look like recommendation sections
        for h3 in soup.find_all('h3'):
            text = h3.get_text(strip=True)
            if text in ['相关文章推荐', '推荐阅读']:
                # Try to find the container div
                container = h3.find_parent('div', class_=lambda c: c and ('mt-16' in c or 'mt-20' in c))
                if container:
                    container.decompose()
                else:
                    # Fallback: check if direct parent is the wrapper
                    if h3.parent.name == 'div' and ('border-t' in h3.parent.get('class', []) or 'mt-16' in h3.parent.get('class', [])):
                        h3.parent.decompose()
    
    # Get cleaned content
    if main_tag:
        main_content = str(main_tag)
    else:
        main_content = str(soup)
        if '<html>' in main_content:
             main_content = soup.find('body').decode_contents() if soup.find('body') else main_content
    
    # --- Dynamic Breadcrumbs Injection (DISABLED) ---
    # current_post = next((p for p in all_posts if p['filepath'] == filepath), None)
    # post_title = current_post['title'] if current_post else '文章详情'
    
    # breadcrumb_html = f'''
    # <nav aria-label="Breadcrumb" class="mb-6">
    #   <ol class="flex items-center space-x-2 text-sm text-slate-400">
    #     <li>
    #       <a href="/" class="hover:text-purple-400 transition">首页</a>
    #     </li>
    #     <li><i class="fa-solid fa-chevron-right text-xs text-slate-600"></i></li>
    #     <li>
    #       <a href="/#blog" class="hover:text-purple-400 transition">教程资源</a>
    #     </li>
    #     <li><i class="fa-solid fa-chevron-right text-xs text-slate-600"></i></li>
    #     <li class="text-slate-200 font-medium truncate max-w-[200px] md:max-w-md" title="{post_title}">
    #       {post_title}
    #     </li>
    #   </ol>
    # </nav>
    # '''
    
    # main_content = breadcrumb_html + '\n' + main_content
    
    # --- Auto Related Posts Injection ---
    # Optimized style to match the screenshot (minimalist, colorful icons, dark background)
    current_post = next((p for p in all_posts if p['filepath'] == filepath), None)
    
    if current_post:
        related_posts = get_related_posts(current_post, all_posts)
        print(f"DEBUG: {filepath} has {len(related_posts)} related posts")
        
        # New card style generation
        cards_html = ""
        for p in related_posts:
             # Trust metadata (now enriched with POST_CONFIG)
             color = p.get('card_color', 'purple')
             icon = p.get('card_icon', 'fa-star')
             
             # Fallback logic only if really needed (e.g. new post not in config)
             if color == 'purple' and icon == 'fa-star':
                 # Cycle through a few nice dark gradients based on hash
                 gradients_list = ['blue', 'emerald', 'orange', 'pink', 'cyan', 'violet']
                 import hashlib
                 idx = int(hashlib.md5(p['title'].encode()).hexdigest(), 16) % len(gradients_list)
                 color = gradients_list[idx]
                 
                 # Map icon based on category
                 if "教程" in p.get('card_category', ''): icon = "fa-book-open"
                 elif "对比" in p.get('card_category', ''): icon = "fa-scale-balanced"
                 elif "优惠" in p.get('card_category', ''): icon = "fa-layer-group"
                 elif "Prompt" in p['title']: icon = "fa-robot"
             
             # Get secondary color for gradient
             secondary_color = GRADIENT_MAP.get(color, 'purple')
             
             cards_html += f'''
            <a href="{p['url']}" class="group block rounded-2xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition">
              <div class="h-28 rounded-xl bg-gradient-to-br from-{color}-600/20 to-{secondary_color}-600/20 flex items-center justify-center text-{color}-400 mb-3">
                <i class="fa-solid {icon} text-3xl"></i>
              </div>
              <div class="text-white font-bold text-sm line-clamp-2">{p['title']}</div>
              <div class="text-slate-500 text-xs mt-1">推荐文章</div>
            </a>
            '''
            
        related_html = f'''
        <div class="mt-16 border-t border-white/10 pt-10">
          <h3 class="text-xl font-bold text-white mb-6">相关文章推荐</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {cards_html}
          </div>
        </div>
        '''
        
        last_main_idx = main_content.rfind('</main>')
        print(f"DEBUG: related_html length: {len(related_html)}, last_main_idx: {last_main_idx}")
        if last_main_idx != -1:
            main_content = main_content[:last_main_idx] + '\n' + related_html + '\n' + main_content[last_main_idx:]
            print(f"DEBUG: Injected related posts into {filepath}")
    # ------------------------------------
    
    new_content = template_content.replace('{{ content }}', main_content)
    new_content = sanitize_links(new_content)
    
    # --- Meta Tags Deep Cleaning ---
    # 1. Remove ecommerce trash
    new_content = re.sub(r'<meta content="[^"]*" name="price"/>', '', new_content)
    new_content = re.sub(r'<meta content="[^"]*" name="currency"/>', '', new_content)
    new_content = re.sub(r'<meta content="[^"]*" name="availability"/>', '', new_content)
    
    # 2. Fix Robots
    new_content = re.sub(r'<meta content="index,follow" name="robots"/>', '', new_content)
    new_content = re.sub(r'<meta content="all" name="robots" />', '', new_content)
    if '</head>' in new_content:
        new_content = new_content.replace('</head>', '<meta content="index, follow, max-image-preview:large" name="robots"/>\n</head>')

    # 3. Remove Baidu Site Verification from Sub-pages (Blog Posts)
    new_content = re.sub(r'<meta[^>]*name="baidu-site-verification"[^>]*/>', '', new_content)

    # 4. Smart Fallback for Social Media (OG/Twitter)
    new_content = re.sub(r'<meta content="website" property="og:type"/>', '<meta content="article" property="og:type"/>', new_content)
    
    if current_post:
        post_url = f"https://gemini-vip.top/blog/{current_post['url']}"
        new_content = re.sub(r'<meta content="[^"]*" property="og:url"/>', f'<meta content="{post_url}" property="og:url"/>', new_content)
        
        new_content = re.sub(r'<link href="[^"]*" hreflang="zh-CN" rel="alternate"/>', f'<link href="{post_url}" hreflang="zh-CN" rel="alternate"/>', new_content)
        
        card_image_match = re.search(r'<meta.*name="card-image".*content="([^"]*)".*>', content)
        og_image = card_image_match.group(1) if card_image_match else 'https://gemini-vip.top/assets/logo.png'
        
        new_content = re.sub(r'<meta content="[^"]*" property="og:image"/>', f'<meta content="{og_image}" property="og:image"/>', new_content)
        new_content = re.sub(r'<meta content="[^"]*" name="twitter:image"/>', f'<meta content="{og_image}" name="twitter:image"/>', new_content)
        
        article_meta = f'''
    <meta property="article:published_time" content="{current_post['date']}" />
    <meta property="article:author" content="Gemini-VIP" />
    <meta property="article:section" content="{current_post['card_category']}" />
    '''
        new_content = new_content.replace('</head>', f'{article_meta}\n</head>')

    src_title = re.search(r'<title>(.*?)</title>', content)
    src_desc = re.search(r'<meta content="([^"]*)" name="description"/>', content)
    if not src_desc:
        src_desc = re.search(r'<meta name="description" content="([^"]*)"/>', content)
    
    src_kw = re.search(r'<meta content="([^"]*)" name="keywords"/>', content)
    if not src_kw:
        src_kw = re.search(r'<meta name="keywords" content="([^"]*)"/>', content)
        
    src_canon = re.search(r'<link href="([^"]*)" rel="canonical"/>', content)
    
    if src_title:
        new_content = re.sub(r'<title>.*?</title>', src_title.group(0), new_content)
    
    if src_desc:
        new_content = re.sub(r'<meta content="[^"]*" name="description"/>', src_desc.group(0), new_content)
        new_content = re.sub(r'<meta name="description" content="[^"]*"/>', src_desc.group(0), new_content)
        
    if src_kw:
        new_content = re.sub(r'<meta content="[^"]*" name="keywords"/>', src_kw.group(0), new_content)
        new_content = re.sub(r'<meta name="keywords" content="[^"]*"/>', src_kw.group(0), new_content)
        
    if src_canon:
        canon_tag = src_canon.group(0)
        if '.html' in canon_tag:
            canon_tag = canon_tag.replace('.html', '')
        new_content = re.sub(r'<link href="[^"]*" rel="canonical"/>', canon_tag, new_content)

    # --- Dynamic JSON-LD Schema Injection ---
    new_content = re.sub(r'<script type="application/ld\+json">.*?</script>', '', new_content, flags=re.DOTALL)

    if current_post:
        post_url = f"https://gemini-vip.top/blog/{current_post['url']}"
        post_date = current_post['date']
        post_desc = current_post['summary']
        if not post_desc:
             post_desc = current_post['title']
             
        schema_json = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": current_post['title'],
            "description": post_desc,
            "datePublished": post_date,
            "dateModified": post_date,
            "url": post_url,
            "author": {
                "@type": "Organization",
                "name": "Gemini-VIP",
                "url": "https://gemini-vip.top/"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Gemini-VIP",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://gemini-vip.top/assets/logo.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": post_url
            },
            "breadcrumb": {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "首页",
                        "item": "https://gemini-vip.top/"
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "教程资源",
                        "item": "https://gemini-vip.top/blog/"
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": current_post['title'],
                        "item": post_url
                    }
                ]
            }
        }
        
        schema_script = f'<script type="application/ld+json">\n{json.dumps(schema_json, indent=2, ensure_ascii=False)}\n</script>'
        
        if '</head>' in new_content:
            new_content = new_content.replace('</head>', f'{schema_script}\n</head>')

    # --- Final Variable Replacement (Fix for {{ title }} bug) ---
    var_title = ''
    var_desc = ''
    
    if current_post:
        var_title = current_post['title']
        var_desc = current_post['summary']
    else:
        # Fallback for pages not in all_posts (like index.html)
        if src_title:
            var_title = src_title.group(1).split(' - ')[0]
        if src_desc:
            var_desc = src_desc.group(1)

    if var_title:
        new_content = new_content.replace('{{ title }}', var_title)
    if var_desc:
        new_content = new_content.replace('{{ description }}', var_desc)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Processed {filepath} - Written successfully")

def scan_and_build_homepage(all_posts):
    print("Building Homepage from Post Metadata...")
    index_file = os.path.join(BLOG_DIR, 'index.html')
    
    if not os.path.exists(index_file):
        print("Missing index.html")
        return

    sorted_posts = sorted(all_posts, key=lambda x: (x.get('card_sticky', 0), x.get('date', '1970-01-01')), reverse=True)
    
    grid_html = ''
    for post in sorted_posts:
        url = post['url']
        title = post['title']
        summary = post.get('summary', '')
        if not summary:
             summary = f"阅读关于 {title} 的详细内容。"
             
        category = post.get('card_category', '教程')
        cat_icon = 'fa-book'
        if '评测' in category: cat_icon = 'fa-chart-simple'
        elif '指南' in category: cat_icon = 'fa-compass'
        elif '优惠' in category or '羊毛' in category: cat_icon = 'fa-gift'
        elif '故障' in category: cat_icon = 'fa-wrench'
        
        icon = post.get('card_icon', 'fa-star')
        color = post.get('card_color', 'purple')
        read_time = post.get('read_time', '3分钟阅读')
        
        secondary_color = GRADIENT_MAP.get(color, 'purple')
        rgba = SHADOW_MAP.get(color, '168,85,247')
        
        card_html = f'''
        <article class="h-full">
          <a class="group block h-full" href="{url}">
            <div class="bg-slate-900/50 border border-white/10 rounded-2xl overflow-hidden h-full hover:border-{color}-500/50 hover:shadow-[0_0_30px_rgba({rgba},0.15)] transition-all duration-300 flex flex-col">
              <div class="h-48 bg-slate-800 relative overflow-hidden">
                <div class="absolute inset-0 bg-gradient-to-br from-{color}-600/20 via-slate-900/50 to-{secondary_color}-600/20 group-hover:scale-105 transition duration-700"></div>
                <div class="absolute inset-0 flex items-center justify-center opacity-30 group-hover:opacity-50 transition">
                  <i class="fa-solid {icon} text-6xl text-{color}-400"></i>
                </div>
                <div class="absolute bottom-4 left-4 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full text-[10px] text-white font-bold border border-white/10">
                  <i class="fa-solid {cat_icon} mr-1 text-{color}-400"></i> {category}
                </div>
              </div>
              <div class="p-6 flex-1 flex flex-col">
                <h3 class="text-xl font-bold text-white mb-3 group-hover:text-{color}-400 transition leading-snug">
                  {title}
                </h3>
                <p class="text-slate-400 text-sm line-clamp-3 mb-4 flex-1 leading-relaxed">
                  {summary}
                </p>
                <div class="text-slate-500 text-xs mt-auto pt-4 border-t border-white/5 flex items-center justify-between">
                  <span><i class="fa-regular fa-clock mr-1"></i> {read_time}</span>
                  <span class="text-{color}-400 group-hover:translate-x-1 transition">阅读全文 →</span>
                </div>
              </div>
            </div>
          </a>
        </article>'''
        grid_html += card_html

    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '{{ featured_grid }}' in content:
        new_content = content.replace('{{ featured_grid }}', grid_html)
    else:
        soup = BeautifulSoup(content, 'html.parser')
        grid_div = soup.find('div', class_='grid grid-cols-1 md:grid-cols-3 gap-8')
        if grid_div:
            grid_div.clear()
            if grid_html.strip():
                # Use html.parser to parse the fragment
                # Wrap in a dummy div to ensure proper parsing of multiple siblings
                grid_soup = BeautifulSoup(f'<div>{grid_html}</div>', 'html.parser')
                # Move children from dummy div to grid_div
                # Use list() to create a copy of children to avoid iteration issues during modification
                for child in list(grid_soup.div.contents):
                    grid_div.append(child)
            else:
                print("Warning: grid_html is empty!")
            
            new_content = str(soup)
        else:
            print("Could not find grid container in index.html to update.")
            return

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Homepage built successfully from Meta Tags.")

def main():
    print("Starting Build Process...")
    if not os.path.exists(TEMPLATE_FILE):
        print("Template file not found!")
        return
    
    template_content = get_template()
    print(f"Template loaded. Length: {len(template_content)}")
    
    if not os.path.exists(BLOG_DIR):
        print(f"Directory {BLOG_DIR} not found!")
        return

    # print("Extracting styles from index...")
    # style_db = extract_styles()

    all_posts = []
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.html') and filename != 'index.html':
             filepath = os.path.join(BLOG_DIR, filename)
             all_posts.append(get_post_metadata(filepath))
    
    for filename in os.listdir(BLOG_DIR):
        if filename.endswith('.html') and filename != 'index.html':
            filepath = os.path.join(BLOG_DIR, filename)
            process_file(filepath, template_content, all_posts)
    
    scan_and_build_homepage(all_posts)
    
    update_indices()

if __name__ == "__main__":
    main()
