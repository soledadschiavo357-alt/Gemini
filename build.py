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
    'gemini-account-purchase-guide': {'color': 'orange', 'icon': 'fa-cart-shopping', 'category': '会员攻略'},
    'gemini-account-appeal-guide': {'color': 'red', 'icon': 'fa-file-shield', 'category': '故障排除'},
    'gemini-registration-guide': {'color': 'cyan', 'icon': 'fa-user-plus', 'category': '新手教程'},
    'gemini-shared-account-guide': {'color': 'orange', 'icon': 'fa-users', 'category': '会员攻略'},
    'how-to-use-gemini-3': {'color': 'indigo', 'icon': 'fa-book-open', 'category': '新手教程'},
    'gemini-veo-video-review': {'color': 'pink', 'icon': 'fa-video', 'category': '视频生成'},
    'gemini-image-generator-guide': {'color': 'pink', 'icon': 'fa-palette', 'category': 'AI绘图'},
    'gemini-banana-guide': {'color': 'yellow', 'icon': 'fa-palette', 'category': 'AI绘图'},
    'gemini-balance-guide': {'color': 'emerald', 'icon': 'fa-server', 'category': 'API教程'},
    'benefits': {'color': 'red', 'icon': 'fa-gift', 'category': '会员权益'},
    'gemini-region-error-fix': {'color': 'slate', 'icon': 'fa-wrench', 'category': '故障排除'},
    'gemini-subscription-error-fix': {'color': 'slate', 'icon': 'fa-circle-exclamation', 'category': '故障排除'},
    'gemini-app-download': {'color': 'blue', 'icon': 'fa-download', 'category': '下载指南'},
    'guide-cn': {'color': 'teal', 'icon': 'fa-language', 'category': '中文指南'},
    'gemini-3-prompt-guide': {'color': 'purple', 'icon': 'fa-wand-magic-sparkles', 'category': 'Prompt教程'},
    'gemini-metaphysics-prompts': {'color': 'indigo', 'icon': 'fa-yin-yang', 'category': 'Prompt教程'},
    'gemini-ppt-prompts': {'color': 'pink', 'icon': 'fa-file-powerpoint', 'category': 'Prompt教程'},
    'gemini-api-key-guide': {'color': 'cyan', 'icon': 'fa-key', 'category': 'API教程'},
    'gemini-quota-guide': {'color': 'cyan', 'icon': 'fa-chart-pie', 'category': 'API教程'},
    'gemini-chrome-guide': {'color': 'blue', 'icon': 'fa-brands fa-chrome', 'category': '新功能'},
    'gemini-generative-ui-guide': {'color': 'pink', 'icon': 'fa-palette', 'category': '新功能'},
    'choose-model-cn': {'color': 'violet', 'icon': 'fa-robot', 'category': '模型选型'},
    'gemini-vs-chatgpt-vs-grok': {'color': 'yellow', 'icon': 'fa-scale-balanced', 'category': '竞品对比'},
    'comparison': {'color': 'yellow', 'icon': 'fa-not-equal', 'category': '竞品对比'},
    'pro-vs-free': {'color': 'green', 'icon': 'fa-circle-half-stroke', 'category': '版本对比'},
    'gemini-notebook-lm-guide': {'color': 'blue', 'icon': 'fa-book-open', 'category': '效率工具'},
    'gemini-remove-watermark-guide': {'color': 'pink', 'icon': 'fa-eraser', 'category': 'AI绘图'}
}

# CTA Banner Configuration
CTA_HTML = """
<div id="cta-banner" class="max-w-3xl mx-auto px-4 sm:px-0 mb-10 mt-6 reveal active">
    <a href="/#pricing" class="group relative block transform hover:-translate-y-1 transition duration-300">
        <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl opacity-40 blur group-hover:opacity-80 transition duration-500"></div>
        
        <div class="relative flex items-center justify-between gap-4 bg-[#0B0F19] p-4 sm:p-5 rounded-xl border border-white/10 shadow-xl">
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1.5">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20 uppercase tracking-wide">
                        <i class="fa-solid fa-crown mr-1"></i> 官方推荐
                    </span>
                    <span class="text-[10px] text-green-400 font-mono animate-pulse flex items-center gap-1">
                        <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span> 自动发货
                    </span>
                </div>
                <h3 class="text-white font-bold text-base sm:text-lg truncate">Gemini 3.0 Pro 独立成品号</h3>
                <p class="text-slate-400 text-xs sm:text-sm truncate mt-0.5">无需申诉 · 独享 2TB 空间 · 稳定防封</p>
            </div>

            <div class="flex flex-col items-end gap-1 shrink-0">
                <div class="bg-white text-black text-xs sm:text-sm font-bold px-4 py-2 rounded-lg group-hover:bg-purple-50 text-center flex items-center gap-1 shadow-lg shadow-white/10">
                    立即获取 <i class="fa-solid fa-arrow-right -rotate-45 group-hover:rotate-0 transition-transform duration-300"></i>
                </div>
            </div>
        </div>
    </a>
</div>
"""

def get_template():
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def get_post_metadata(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Title Priority: <h1> -> <title>
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    if h1_match:
        # Remove HTML tags from h1
        title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
        # Collapse multiple spaces
        title = ' '.join(title.split())
    else:
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

# Global state to track recommendation frequency for SEO balancing
INCOMING_LINK_COUNTS = {}

def get_related_posts(current_post, all_posts):
    # Filter out current post
    candidates = [p for p in all_posts if p['url'] != current_post['url']]
    
    scored_candidates = []
    current_tags = set(current_post['tags'])
    
    for p in candidates:
        other_tags = set(p['tags'])
        overlap = len(current_tags.intersection(other_tags))
        
        # Initialize count if not exists
        if p['url'] not in INCOMING_LINK_COUNTS:
            INCOMING_LINK_COUNTS[p['url']] = 0
            
        scored_candidates.append({
            'post': p,
            'overlap': overlap
        })
    
    # Intelligent SEO Sorting Strategy:
    # 1. Relevance (Overlap): High overlap is still the most important factor.
    # 2. Balance (Incoming Links): If overlap is same, prioritize posts with FEWER incoming links.
    #    This ensures "wealth distribution" so new or niche posts get visibility.
    # 3. Freshness (Date): If everything else is equal, prefer newer content.
    # 4. Randomness: Add a tiny bit of random shuffle for same-score items to avoid static patterns? 
    #    (Python's sort is stable, so we rely on the keys)
    
    scored_candidates.sort(key=lambda x: (
        x['overlap'],                       # Primary: Relevance
        -INCOMING_LINK_COUNTS[x['post']['url']], # Secondary: Balance (Less links = Higher priority? Wait, we want fewer links to be higher. So negative count is bad? No.)
        # Sort is ascending by default? No, we used reverse=True before.
        # Let's standardize to reverse=True (Descending score).
        # We want: Higher Overlap -> Higher Score
        # We want: Lower Link Count -> Higher Score
        # We want: Newer Date -> Higher Score
        x['post']['date']
    ), reverse=True)
    
    # Wait, the logic above for Link Count is tricky with reverse=True.
    # If reverse=True:
    #   Overlap 3 > Overlap 1 (Good)
    #   Link Count 5 vs Link Count 20. We want 5 to be picked.
    #   If we use -Count: -5 > -20. So -Count works with reverse=True.
    
    # Refined Sort Key:
    scored_candidates.sort(key=lambda x: (
        x['overlap'],                               # 1. Relevance (High is good)
        -INCOMING_LINK_COUNTS[x['post']['url']],    # 2. Balance (Low count -> High negative number? No. Low count 0 -> 0. High count 10 -> -10. 0 > -10. So Yes, -Count works.)
        x['post']['date']                           # 3. Freshness (Newer is string-larger usually)
    ), reverse=True)
    
    # Select top 4
    selected = [x['post'] for x in scored_candidates[:4]]
    
    # Update global counts
    for p in selected:
        INCOMING_LINK_COUNTS[p['url']] += 1
        
    return selected

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
    <a class="group block rounded-2xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition" href="/blog/{url}">
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
    # 1. Handle ../index specific cases (Legacy priority)
    def replace_relative_index(match):
        anchor = match.group(1) or ''
        return f'href="/{anchor}"'
    
    html_content = re.sub(r'href="(?:\.\./)+index\.html(#[^"]*)?"', replace_relative_index, html_content)
    html_content = re.sub(r'href="(?:\.\./)+index(#[^"]*)?"', replace_relative_index, html_content)

    # 2. General Link Sanitizer
    def general_fix(match):
        url = match.group(1)
        
        # Skip external/special/absolute/placeholders
        if url.startswith(('http:', 'https:', 'mailto:', 'tel:', '//', '#', 'javascript:', 'data:', '/', '{{')):
            return match.group(0)
            
        # Handle parent refs ../
        if url.startswith('../'):
             # Strip .html if present
             if url.endswith('.html'):
                 url = url[:-5]
             
             # Resolve parent ref: ../foo -> /foo
             clean_path = url.replace('../', '')
             if clean_path == 'index': return 'href="/"'
             return f'href="/{clean_path}"'
        
        # Handle current dir (blog/) refs
        # Strip .html if present
        if url.endswith('.html'):
            url = url[:-5]
            
        if url == 'index':
            return 'href="/blog/"'
            
        return f'href="/blog/{url}"'

    html_content = re.sub(r'href="([^"]+)"', general_fix, html_content)
    
    # 3. Canonical Link Fix
    def fix_canonical(match):
        url = match.group(1)
        return f'<link href="{url}" rel="canonical"/>'
    
    html_content = re.sub(r'<link href="([^"]+)\.html" rel="canonical"/>', fix_canonical, html_content)
    
    return html_content

def update_indices():
    print("Updating indices...")
    update_sitemap.main()

def optimize_sales_card(soup):
    """
    Optimizes the sidebar sales card to be more compact.
    """
    # Find the sales card by its unique title
    # Relaxed regex to match "Gemini 3.0 Pro 成品号" or "Gemini Pro 会员成品号"
    card_title = soup.find('h3', string=re.compile(r'Gemini.*Pro.*成品号'))
    if not card_title:
        # Fallback: Try matching just "成品号" if the prefix changes
        card_title = soup.find('h3', string=re.compile(r'.*成品号'))
    
    main_container = None
    
    if card_title:
        # Go up to the container (h3 -> div -> div)
        # The structure is: div > div > h3
        card_container = card_title.parent
        if card_container:
            # The main container is the parent of the card_container
            # <div class="relative bg-[#0B0F19] ...">
            main_container = card_container
            if 'bg-[#0B0F19]' not in str(main_container.get('class', [])):
                # Try one level up if we didn't hit the bg container
                main_container = card_container.parent

    if not main_container or 'bg-[#0B0F19]' not in str(main_container.get('class', [])):
        # Fallback: find by class if traversal failed or title not found
        # Strategy: Find div with the unique sales card background color
        main_container = soup.find('div', class_=lambda c: c and 'bg-[#0B0F19]' in c)
    
    if not main_container:
        return soup

    # 1. Reduce Padding of the main container (p-6 -> p-5)
    # Compromise: p-6 is too tall, p-4 is too short/empty.
    # Let's try p-5 (20px).
    if main_container.has_attr('class'):
        # Further reduce vertical padding to compensate for the larger top offset
        # p-5 -> px-5 py-4 (Keep horizontal width, reduce vertical height)
        # This is a precision strike to reduce height without making it look "thin" horizontally.
        new_classes = []
        has_p = False
        for c in main_container['class']:
             if c == 'p-6' or c == 'p-5' or c == 'p-4':
                  new_classes.append('px-5')
                  new_classes.append('py-4')
                  has_p = True
             else:
                  new_classes.append(c)
        if not has_p: # Fallback if no padding class found (unlikely)
             new_classes.append('px-5')
             new_classes.append('py-4')
        
        # User confirmed: "gemini-balance-guide.html" looks perfect.
        # We need to make sure this logic produces EXACTLY what that page has.
        # Currently, build.py produces: px-5 py-4.
        # And the template (gemini-balance-guide.html) has: px-5 py-4 (verified in source).
        # So this logic is CORRECT.
        
        main_container['class'] = new_classes

    # 2. Optimize Header (Badge Row)
    # Select by unique combination of classes
    badge_row = main_container.select_one('.flex.justify-between.items-center')
    if badge_row and badge_row.has_attr('class'):
        # mb-6 -> mb-4 (Compromise)
        badge_row['class'] = [c.replace('mb-6', 'mb-4') for c in badge_row['class']]

    # 3. Optimize Icon Container
    # Find the div that has h-32
    icon_container = main_container.find('div', class_=lambda c: c and ('h-32' in c or 'h-14' in c))
    if icon_container and icon_container.has_attr('class'):
        # h-32 -> h-20 (80px), mb-6 -> mb-4
        # This keeps the icon prominent but saves vertical space.
        new_classes = []
        for c in icon_container['class']:
            if c == 'h-32' or c == 'h-14': new_classes.append('h-20')
            elif c == 'mb-6' or c == 'mb-2': new_classes.append('mb-4')
            else: new_classes.append(c)
        icon_container['class'] = new_classes
        
        # Optimize Icon Size (text-5xl -> text-4xl)
        icon = icon_container.find('i')
        if icon and icon.has_attr('class'):
             icon['class'] = [c.replace('text-5xl', 'text-4xl').replace('text-2xl', 'text-4xl') for c in icon['class']]

    # 4. Optimize Subtitle (mb-6 -> mb-4, pb-4 -> pb-3)
    subtitle = main_container.find('p', class_=lambda c: c and 'text-xs' in c and 'border-b' in c)
    if subtitle and subtitle.has_attr('class'):
        new_classes = []
        for c in subtitle['class']:
            if c == 'mb-6': new_classes.append('mb-4')
            elif c == 'pb-4': new_classes.append('pb-3')
            else: new_classes.append(c)
        subtitle['class'] = new_classes

    # 5. Optimize Price Area (mb-6 -> mb-4)
    price_area = main_container.select_one('.flex.items-end.justify-between')
    if price_area and price_area.has_attr('class'):
        price_area['class'] = [c.replace('mb-6', 'mb-4') for c in price_area['class']]
        
        # Keep Price Size Big (text-3xl)
        price_text = price_area.find('div', class_=lambda c: c and ('text-3xl' in c or 'text-2xl' in c))
        if price_text and price_text.has_attr('class'):
             price_text['class'] = [c.replace('text-2xl', 'text-3xl') for c in price_text['class']]

    # 6. Optimize Features List (mb-6 -> mb-4, space-y-3 -> space-y-2)
    features = main_container.find('ul', class_=lambda c: c and ('space-y-3' in c or 'space-y-2' in c))
    if features and features.has_attr('class'):
        new_classes = []
        for c in features['class']:
            if c == 'mb-6': new_classes.append('mb-4')
            elif c == 'space-y-3': new_classes.append('space-y-2')
            else: new_classes.append(c)
        features['class'] = new_classes

    # 7. Optimize Copy Code (mb-6 -> mb-4)
    copy_code = main_container.find('div', onclick=True)
    if copy_code and copy_code.has_attr('class'):
        copy_code['class'] = [c.replace('mb-6', 'mb-4') for c in copy_code['class']]
        
    # 8. Optimize CTA Button (Wrapper Link & Inner Link)
    
    # Case A: The card is wrapped in an <a> tag (Common in "Top Card" design)
    if main_container.parent and main_container.parent.name == 'a':
        wrapper_a = main_container.parent
        if wrapper_a.has_attr('href') and '/#pricing' in wrapper_a['href']:
             wrapper_a['href'] = '/#pricing'

    # Case B: The link is inside the card (Common in "Sidebar" design)
    # Use regex to find ALL buttons even if they have query params
    cta_btns = main_container.find_all('a', href=re.compile(r'/#pricing'))
    for cta_btn in cta_btns:
        if cta_btn.has_attr('class'):
            # Force clean URL
            cta_btn['href'] = '/#pricing'
            
            # Restore original padding: py-3.5
            # User Feedback: "CTA button too big again".
            # Revert py-4 back to py-3.5.
            # Also maybe remove text-lg if it makes it look too chunky.
            
            # Remove any existing py- classes
            new_classes = [c for c in cta_btn['class'] if not c.startswith('py-')]
            new_classes.append('py-3.5')
            
            # Remove text-lg if present, to reduce "bigness"
            if 'text-lg' in new_classes:
                 new_classes.remove('text-lg')
                 
            # Keep font-bold as it looks good
            if 'font-bold' not in new_classes:
                 new_classes.append('font-bold')
                 
            cta_btn['class'] = new_classes

    # 9. Optimize Guarantee Text (mt-4 -> mt-3)
    guarantee = main_container.find('div', class_=lambda c: c and ('mt-4' in c or 'mt-3' in c or 'mt-2' in c) and 'text-center' in c)
    if guarantee and guarantee.has_attr('class'):
        new_classes = []
        for c in guarantee['class']:
            if c == 'mt-2' or c == 'mt-3': new_classes.append('mt-4')
            else: new_classes.append(c)
        guarantee['class'] = new_classes

    # 10. Optimize Sticky Container Position (Breathing Room)
    # Find the parent sticky container
    # Traverse up to find the sticky container
    sticky_container = main_container
    found_sticky = False
    for _ in range(3): # Try going up 3 levels
        if sticky_container and sticky_container.parent:
            sticky_container = sticky_container.parent
            if sticky_container.has_attr('class') and 'sticky' in str(sticky_container['class']):
                found_sticky = True
                break
    
    if found_sticky:
        new_sticky_classes = []
        for c in sticky_container['class']:
            # top-24 -> top-32 (Avoid touching header on scroll)
            # User reported overlay issue with header.
            # Header height is usually around 64px-80px.
            # If we use top-20 (80px), it might be barely touching.
            # If we use top-24 (96px), it's safer.
            # If we use top-28 (112px) or top-32 (128px), it's definitely safe.
            # Previously we reduced it to top-20 to fix the "bottom hidden" issue.
            # But now it overlaps the header.
            # We MUST increase top offset to avoid overlap.
            # Let's go back to top-28 (112px) or top-32 (128px).
            # AND we must solve the "bottom hidden" issue by making the card SHORTER.
            
            # User says: "现在这个销售卡片顶部到header导航栏距离不错... 问题是现在滑动洁面 距离又要调整 有没有办法 不要在调整距离了 随着页面固定好就可以了"
             # The user likes the INITIAL gap.
             # But when scrolling, the card "adjusts" (moves up or down) to hit the sticky point.
             # The user wants the gap to be CONSTANT.
             # This means the sticky offset (top-XX) must VISUALLY MATCH the initial gap relative to the viewport/header.
             
             # Currently: top-28 (112px).
             # Initial Gap: mt-12 (48px) from element above.
             # Header height is the key variable here.
             # If Header is ~80px.
             # Sticky Top Position relative to viewport = 112px.
             # Gap below header = 112px - 80px = 32px.
             
             # Initial Position relative to viewport (before scroll):
             # Header (80px) + Breadcrumbs/Title Section (variable) + mt-12 (48px).
             # Wait, the card is in the sidebar. Its top is aligned with the article content.
             # The article content usually has some top padding/margin.
             
             # If the user says "Don't adjust distance when sliding", they mean:
             # When the scroll passes the point where the card *would* stick,
             # the card should just stay exactly where it is visually relative to the header, 
             # without jumping up or down.
             
             # This implies that 'top-XX' should be exactly equal to the distance from the top of the viewport to the top of the card in its natural position.
             # Since we don't know the exact pixel height of the header + top spacing, we have to guess or use a larger value.
             
             # However, the user previously rejected top-36 (144px).
             # And they accepted top-28 (112px) as "good distance".
             # But they complain about "distance adjusting" during scroll.
             
             # Maybe the issue is that top-28 is TOO SMALL compared to the initial position?
             # Or TOO LARGE?
             # If it jumps UP, top-28 is too small.
             # If it jumps DOWN, top-28 is too large.
             
             # "不要在调整距离了" -> Don't change the gap.
             # This strongly suggests using a larger 'top' value so it sticks LATER, matching the visual flow.
             # But I already tried top-36 and they said "Don't adjust".
             # Wait, maybe they meant "Don't change it AGAIN" (referring to my previous change)?
             # "现在这个...距离不错...问题是...距离又要调整" -> The "adjustment" happens DURING SCROLL.
             
             # Let's try to set 'top-32' (128px).
             # It's between top-28 (112px) and top-36 (144px).
             # 128px - 80px = 48px gap.
             # This matches mt-12 (48px) perfectly!
             # So top-32 is theoretically the "Magic Number" for consistency.
             
             if c == 'top-24' or c == 'top-20' or c == 'top-32' or c == 'top-36' or c == 'top-28': new_sticky_classes.append('top-32') 
             else: new_sticky_classes.append(c)
        
        # Ensure mt-12 is present for initial spacing
        # User Feedback: "间距 是不是有变化了 不能固定嘛？"
        # The user feels the spacing is changing or inconsistent.
        # This might be because mt-12 (margin-top) scrolls with the element, but top-28 (sticky offset) only applies when stuck.
        # If the user wants the GAP to be CONSTANT between the header and the card, regardless of scroll state:
        # 1. Initial state: The card is below the header. The gap is determined by the layout flow (margin).
        # 2. Sticky state: The card is stuck. The gap is determined by 'top-28'.
        
        # If the initial gap (mt-12 + flow) != sticky gap (top-28), the card will "jump" or shift visually when it hits the sticky point.
        # Header height ~ 80px.
        # Sticky top-28 = 112px from viewport top.
        # So the gap from header bottom to card top = 112px - 80px = 32px.
        
        # Initial state:
        # The card is inside a column.
        # If we use mt-12 (48px), the initial gap is 48px from the element above it.
        # If the element above it is the breadcrumb/title row which is aligned with the top,
        # then the visual gap might be consistent.
        
        # However, the user says "就算向下滑动 间距也不要变化了".
        # This implies the sticky position (top-28) should VISUALLY MATCH the initial top margin relative to the viewport/header.
        # If the card starts at Y=150px, and the header is 80px, the gap is 70px.
        # When you scroll, if the card sticks at Y=112px, the gap shrinks to 32px. This is a CHANGE.
        # To fix this, we need to make the sticky position match the visual gap the user likes.
        
        # If the user likes the "current" gap (which they saw in the screenshot),
        # and complained about it changing when scrolling.
        # We need to increase 'top' to match the initial visual position.
        # Let's try top-32 (128px) or even more.
        # 128px - 80px (header) = 48px gap.
        # This matches mt-12 (48px).
        # So if we set top-32 or top-36, it might feel more "fixed".
        
        if 'mt-12' not in new_sticky_classes:
             if 'mt-6' in new_sticky_classes:
                  new_sticky_classes = [c.replace('mt-6', 'mt-12') for c in new_sticky_classes]
             else:
                  new_sticky_classes.append('mt-12')
            
        # User says: "Sales card bottom overlaps with webpage bottom/footer. No breathing room."
        # We need to add margin-bottom to the sticky container.
        # This will ensure that when the user scrolls to the bottom, the card pushes against the footer or next section with some gap.
        if 'mb-12' not in new_sticky_classes:
             # Actually, mb-12 on the sticky element might not work if the parent container height is limiting.
             # The better fix (which we applied manually) is to add pb-32 to the <aside> container.
             # Let's try to apply that here too.
             # Traverse up to find <aside>
             aside_container = sticky_container.parent
             if aside_container and aside_container.name == 'aside':
                 if aside_container.has_attr('class'):
                     if 'pb-32' not in aside_container['class']:
                         aside_container['class'].append('pb-32')
                 else:
                     aside_container['class'] = ['pb-32']
             
             # Still keep mb-12 on sticky just in case
             # new_sticky_classes.append('mb-12') 
             # Update: We removed mb-12 in manual fix because pb-32 handles it better.
             # So let's NOT add mb-12 if we successfully added pb-32.
             pass
             
        sticky_container['class'] = new_sticky_classes

    # Optimize the last element's bottom margin inside the card to reduce empty space
    # Find the last child div
    last_div = main_container.find_all('div', recursive=False)[-1] if main_container.find_all('div', recursive=False) else None
    if last_div and last_div.has_attr('class'):
         # If it has mt-4, maybe reduce it?
         # The code has: <div class="mt-4 text-center">...</div>
         # Let's change mt-4 to mt-2 for the footer/guarantee text
         pass # Already handled in step 9 (mt-4 -> mt-3)

    return soup

    return soup

def enforce_seo_rules(soup):
    """
    Enforces SEO rules:
    1. Adds rel="nofollow sponsored noopener noreferrer" to all /go/ links.
    2. Enforces Pyramid Model: Replaces Sales CTAs pointing to /go/xxx with /#pricing.
    """
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # Rule 1: Affiliate Link Attributes
        if href.startswith('/go/'):
            # Ensure correct rel attributes
            rel = a.get('rel', [])
            # Normalize rel to list if it's a string
            if isinstance(rel, str):
                rel = rel.split()
            
            required_rels = ['nofollow', 'sponsored', 'noopener', 'noreferrer']
            for r in required_rels:
                if r not in rel:
                    rel.append(r)
            a['rel'] = rel
            
            # Rule 2: Pyramid Model Enforcement (Sales CTA -> Homepage)
            # Check if this looks like a primary CTA button
            text = a.get_text(strip=True)
            # Keywords that imply a direct purchase action
            cta_keywords = ['立即开通', '立即购买', '立即上车', '查看方案', '获取API', '立即升级', '查看价格']
            
            # Check if text matches keywords OR if it has button-like classes
            is_cta_text = any(kw in text for kw in cta_keywords)
            
            # Simplified check: If it's a /go/ link AND has CTA text, redirect to pricing
            # Exception: API links might need to go to /go/api directly if specific, but generally #pricing is safer for weight
            # Exception: "获取 API 额度" usually goes to #pricing too in our model
            
            if is_cta_text and href != '/#pricing':
                # Check for specific exceptions? 
                # For now, enforce pyramid model strictly for these keywords
                print(f"  [SEO Auto-Fix] Redirecting CTA '{text}' from {href} to /#pricing")
                a['href'] = '/#pricing'

        # Rule 3: Clean up UTM and other params from internal pricing links
        if '/#pricing' in href:
            if '?' in href:
                print(f"  [SEO Auto-Fix] Cleaning pricing link from {href} to /#pricing")
                a['href'] = '/#pricing'

    return soup

def inject_cta_banner(soup):
    """
    智能插入 CTA 横幅：
    1. 优先尝试插入到 <header> 之后（最佳位置）。
    2. 如果没有 <header>，则尝试插入到正文容器 <div class="prose ..."> 之前（兼容模式）。
    3. 如果还是找不到，则尝试插入到 <h1> 标题之后（保底模式）。
    """
    # 0. 防止重复插入
    if soup.find(id="cta-banner"):
        return soup

    cta_soup = BeautifulSoup(CTA_HTML, 'html.parser')
    
    # 策略 A: 标准模式 (找 header)
    article = soup.find('article')
    if article:
        header = article.find('header')
        if header:
            header.insert_after(cta_soup)
            print("  [Inject] CTA inserted after <header>.")
            return soup

    # 策略 B: 兼容模式 (找 prose 正文容器)
    # prose 类名通常是正文的开始，插在它前面通常就是标题下面
    prose_div = soup.find('div', class_=lambda c: c and 'prose' in c)
    if prose_div:
        prose_div.insert_before(cta_soup)
        print("  [Inject] CTA inserted before <div class='prose'>.")
        return soup

    # 策略 C: 保底模式 (找 h1)
    h1 = soup.find('h1')
    if h1:
        h1.insert_after(cta_soup)
        print("  [Inject] CTA inserted after <h1>.")
        return soup

    print("  [Warning] No suitable location found for CTA banner.")
    return soup

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
        
        # --- Optimize Sales Card ---
        soup = optimize_sales_card(soup)
        
        # --- Enforce SEO Rules (New) ---
        soup = enforce_seo_rules(soup)
        
        # =========== 新增：插入 CTA 卡片 ===========
        soup = inject_cta_banner(soup)
        # ========================================
        
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
            <a href="/blog/{p['url']}" class="group block rounded-2xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 transition">
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
    var_kw = ''
    var_canon = ''
    
    if current_post:
        var_title = current_post['title']
        var_desc = current_post['summary']
        if current_post['tags']:
            var_kw = ', '.join(current_post['tags'])
        var_canon = f"https://gemini-vip.top/blog/{current_post['url']}"
    else:
        # Fallback for pages not in all_posts (like index.html)
        if src_title:
            var_title = src_title.group(1).split(' - ')[0]
        if src_desc:
            var_desc = src_desc.group(1)
        if src_kw:
            # Extract content from src_kw tag
            m = re.search(r'content="([^"]*)"', src_kw.group(0))
            if m: var_kw = m.group(1)
        if src_canon:
            m = re.search(r'href="([^"]*)"', src_canon.group(0))
            if m: var_canon = m.group(1)

    if var_title:
        new_content = new_content.replace('{{ title }}', var_title)
    if var_desc:
        new_content = new_content.replace('{{ description }}', var_desc)
    if var_kw:
        new_content = new_content.replace('{{ keywords }}', var_kw)
    else:
         # Clean up empty placeholder if no keywords
        new_content = new_content.replace('{{ keywords }}', '')
        
    if var_canon:
        # Ensure canonical is full URL or absolute path
        if not var_canon.startswith('http'):
             if not var_canon.startswith('/'):
                 var_canon = '/' + var_canon
             var_canon = f"https://gemini-vip.top{var_canon}"
        new_content = new_content.replace('{{ canonical }}', var_canon)
    else:
         # Fallback to current URL if no canonical provided
         if current_post:
             new_content = new_content.replace('{{ canonical }}', f"https://gemini-vip.top/blog/{current_post['url']}")
         else:
             new_content = new_content.replace('{{ canonical }}', '')

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
        <article class="h-full" data-category="{category}">
          <a class="group block h-full" href="/blog/{url}">
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

    # --- Update Last Updated Date ---
    # Find the latest date from all posts
    all_dates = [p.get('date', '1970-01-01') for p in all_posts]
    if all_dates:
        latest_date = max(all_dates)
        print(f"Updating Homepage Last Updated Date to: {latest_date}")
        
        # Regex to replace the timestamp
        # Matches: <div class="mt-2 text-xs text-slate-500">最后更新：<time datetime="...">...</time></div>
        date_pattern = r'<div class="mt-2 text-xs text-slate-500">\s*最后更新：\s*<time datetime="[^"]*">[^<]*</time>\s*</div>'
        new_date_html = f'<div class="mt-2 text-xs text-slate-500">最后更新：<time datetime="{latest_date}">{latest_date}</time></div>'
        
        if re.search(date_pattern, content):
            content = re.sub(date_pattern, new_date_html, content)
        else:
            print("Warning: Could not find 'Last Updated' div in blog/index.html to update.")
    # --------------------------------
    
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

    # --- Update JSON-LD CollectionPage ---
    print("Updating JSON-LD CollectionPage...")
    json_items = []
    for i, post in enumerate(sorted_posts, 1):
        full_url = f"https://gemini-vip.top/blog/{post['url']}"
        post_desc = post.get('summary', '')
        if not post_desc:
             post_desc = post['title']
             
        item = {
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "BlogPosting",
                "@id": full_url,
                "url": full_url,
                "name": post['title'],
                "headline": post['title'],
                "description": post_desc,
                "datePublished": post.get('date', ''),
                "author": {
                    "@type": "Organization",
                    "name": "Gemini-VIP"
                },
                "image": "https://gemini-vip.top/assets/logo.png"
            }
        }
        json_items.append(item)
    
    collection_page_json = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Gemini 教程与评测合集",
        "description": "Google Gemini 相关教程、评测、指南聚合页",
        "url": "https://gemini-vip.top/blog/",
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": json_items
        },
        "publisher": {
            "@type": "Organization",
            "name": "Gemini-VIP",
            "logo": {
                "@type": "ImageObject",
                "url": "https://gemini-vip.top/assets/logo.png",
                "width": 512,
                "height": 512
            }
        }
    }

    new_script_block = f'<script type="application/ld+json">\n{json.dumps(collection_page_json, ensure_ascii=False, indent=2)}\n</script>'
    
    # Robust replacement of the entire CollectionPage script block
    # Matches <script ...> ... "@type": "CollectionPage" ... </script>
    pattern = r'<script type="application/ld\+json">\s*\{[\s\S]*?"@type":\s*"CollectionPage"[\s\S]*?\}\s*</script>'
    
    if re.search(pattern, new_content):
        new_content = re.sub(pattern, lambda m: new_script_block, new_content, count=1)
        print("Updated existing CollectionPage JSON-LD.")
    else:
        print("Warning: CollectionPage JSON-LD block not found. Inserting new one.")
        if '</head>' in new_content:
             new_content = new_content.replace('</head>', f'{new_script_block}\n</head>')
    
    # --- Update Hreflang for Blog Index ---
    print("Updating Hreflang for Blog Index...")
    new_content = re.sub(
        r'<link href="[^"]*" hreflang="zh-CN" rel="alternate"/>', 
        '<link href="https://gemini-vip.top/blog/" hreflang="zh-CN" rel="alternate"/>', 
        new_content
    )
    # --------------------------------------

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Homepage built successfully from Meta Tags.")

def update_root_homepage(all_posts):
    print("Updating Root Homepage (index.html)...")
    root_index_file = 'index.html'
    
    if not os.path.exists(root_index_file):
        print("Missing root index.html")
        return

    # Sort and take top 6
    sorted_posts = sorted(all_posts, key=lambda x: (x.get('card_sticky', 0), x.get('date', '1970-01-01')), reverse=True)[:6]
    
    grid_html = ''
    for post in sorted_posts:
        url = f"/blog/{post['url']}" # Prepend /blog/ for root index
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
        </a>'''
        grid_html += card_html

    with open(root_index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find the #blog section
    blog_section = soup.find('section', id='blog')
    if blog_section:
        grid_div = blog_section.find('div', class_='grid grid-cols-1 md:grid-cols-3 gap-8')
        if grid_div:
            grid_div.clear()
            if grid_html.strip():
                # Use html.parser to parse the fragment
                grid_soup = BeautifulSoup(f'<div>{grid_html}</div>', 'html.parser')
                for child in list(grid_soup.div.contents):
                    grid_div.append(child)
            else:
                print("Warning: root grid_html is empty!")
            
            new_content = str(soup)
            # Fix soup prettify issues if any (BeautifulSoup might mess up some void tags or formatting, but usually okay for this)
            # Just writing str(soup) is usually safer than prettify() for preserving scripts/styles
            
            with open(root_index_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Root Homepage updated successfully.")
        else:
            print("Could not find grid container in root index.html")
    else:
        print("Could not find #blog section in root index.html")



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
    update_root_homepage(all_posts)
    
    update_indices()

if __name__ == "__main__":
    main()
