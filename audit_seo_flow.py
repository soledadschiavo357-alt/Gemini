import os
import re
import sys
from html.parser import HTMLParser
from collections import defaultdict, deque
from urllib.parse import urlparse, urljoin

# Configuration
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR = os.path.join(ROOT_DIR, 'blog')
EXTENSIONS = {'.html'}

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = [] # (href, rel, text, classes)
        self.current_link = None
        
        # Metadata
        self.page_title = None
        self.page_description = None
        self._in_title = False
        self._title_buffer = []

    def handle_starttag(self, tag, attrs):
        # Metadata Extraction
        if tag == 'title':
            self._in_title = True
            self._title_buffer = []
        elif tag == 'meta':
            # Check for description
            # Convert attrs to dict for easier access
            attrs_dict = {k.lower(): v for k, v in attrs if v is not None}
            if attrs_dict.get('name', '').lower() == 'description':
                self.page_description = attrs_dict.get('content', '').strip()

        # Link Extraction
        if tag == 'a':
            href = None
            rel = None
            classes = set()
            for attr, value in attrs:
                if attr == 'href':
                    href = value
                elif attr == 'rel':
                    rel = value
                elif attr == 'class':
                    classes = set(value.split())
            
            if href:
                self.current_link = {
                    'href': href,
                    'rel': rel,
                    'classes': classes,
                    'text': []
                }

    def handle_data(self, data):
        # Metadata
        if self._in_title:
            self._title_buffer.append(data)

        # Link
        if self.current_link is not None:
            self.current_link['text'].append(data)

    def handle_endtag(self, tag):
        # Metadata
        if tag == 'title':
            self._in_title = False
            full_title = ''.join(self._title_buffer).strip()
            if full_title:
                self.page_title = full_title
        
        # Link
        if tag == 'a' and self.current_link is not None:
            full_text = ''.join(self.current_link['text']).strip()
            self.links.append((
                self.current_link['href'],
                self.current_link['rel'],
                full_text,
                self.current_link['classes']
            ))
            self.current_link = None

def get_files_to_scan():
    files = []
    # Scan root
    for f in os.listdir(ROOT_DIR):
        if f.endswith('.html'):
            files.append(os.path.join(ROOT_DIR, f))
    
    # Scan blog/
    if os.path.exists(BLOG_DIR):
        for f in os.listdir(BLOG_DIR):
            if f.endswith('.html'):
                files.append(os.path.join(BLOG_DIR, f))
    
    # Exclude layout templates
    files = [f for f in files if 'layout_template' not in f]
    
    return files

def parse_sitemap():
    sitemap_path = os.path.join(ROOT_DIR, 'sitemap.xml')
    if not os.path.exists(sitemap_path):
        return set()
    
    urls = set()
    try:
        with open(sitemap_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple regex to extract locs
            locs = re.findall(r'<loc>(.*?)</loc>', content)
            for loc in locs:
                # Strip domain
                path = loc.replace('https://gemini-vip.top', '')
                if path == '': path = '/'
                urls.add(path)
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
    return urls

def parse_redirects():
    redirects_path = os.path.join(ROOT_DIR, '_redirects')
    redirect_sources = set()
    if not os.path.exists(redirects_path):
        return redirect_sources
    
    try:
        with open(redirects_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    source = parts[0]
                    redirect_sources.add(source)
    except Exception as e:
        print(f"Error parsing _redirects: {e}")
    return redirect_sources

def file_path_to_url(file_path):
    rel_path = os.path.relpath(file_path, ROOT_DIR)
    
    if rel_path == 'index.html':
        return '/'
    
    parts = rel_path.split(os.sep)
    
    # Handle blog/index.html -> /blog/
    if parts[-1] == 'index.html':
        return '/' + '/'.join(parts[:-1]) + '/'
    
    # Handle other .html files -> remove extension
    if parts[-1].endswith('.html'):
        parts[-1] = parts[-1][:-5]
    
    return '/' + '/'.join(parts)

def normalize_link(source_url, href):
    # Remove anchor/query
    href = href.split('#')[0].split('?')[0]
    if not href:
        return None
        
    # Ignore external links
    if href.startswith(('http:', 'https:', 'mailto:', 'tel:', 'javascript:')):
        return None
        
    # Resolve relative paths
    # Note: simple urljoin works well for absolute paths (start with /) too
    # We treat source_url as the base. 
    # If source_url is /blog/post, it effectively is /blog/post.html or /blog/post/ directory context?
    # Browsers treat /blog/post as a file, so "link" is relative to /blog/.
    # But if source is /blog/ (directory), "link" is relative to /blog/.
    
    # To use urljoin correctly, we need to know if the source acts as a directory.
    # Our file_path_to_url logic:
    # / -> /
    # /blog/ -> /blog/
    # /about -> /about
    
    # Python's urljoin behavior:
    # urljoin('/about', 'contact') -> '/contact' (replaces 'about')
    # urljoin('/about/', 'contact') -> '/about/contact'
    
    # This matches browser behavior for clean URLs WITHOUT trailing slash.
    # If we are at /about, and click 'contact', we go to /contact.
    # If we are at /blog/post, and click 'related', we go to /blog/related.
    
    full_url = urljoin(source_url, href)
    
    # Normalize trailing slashes for consistency in graph
    # If it ends in slash, keep it. If not, keep it.
    # But we need to match the canonical URLs we generated.
    # Our canonical generator produces:
    # /
    # /blog/
    # /about
    # /blog/post
    
    # If the link is /about/, but our canonical is /about, we should normalize.
    # Let's strip trailing slash if it's not root, or match exact canonicals later.
    # Actually, let's keep it as is and try to match.
    
    return full_url

def main():
    print("🚀 Starting SEO Flow Audit...")
    
    files = get_files_to_scan()
    print(f"Found {len(files)} HTML files to scan.")
    
    # Map Canonical URL -> File Path
    url_to_file = {}
    for f in files:
        url = file_path_to_url(f)
        url_to_file[url] = f
    
    # Get Sitemap URLs
    sitemap_urls = parse_sitemap()
    print(f"Found {len(sitemap_urls)} URLs in sitemap.xml.")
    
    # Get Redirects
    redirect_urls = parse_redirects()
    print(f"Found {len(redirect_urls)} redirects in _redirects.")

    # Graph Data
    out_links = defaultdict(set) # url -> set(target_urls)
    in_links = defaultdict(set)  # url -> set(source_urls)
    dirty_links = [] # (source_file, link)
    broken_links = [] # (source_url, target_url)
    external_links = defaultdict(list) # target_domain -> list(source_urls)
    redirect_usage = defaultdict(list) # redirect_url -> list((source_url, rel))
    pyramid_violations = [] # (source_file, link_text, href)
    
    # TDK Data
    page_titles = {} # url -> title
    page_descriptions = {} # url -> description
    duplicate_titles = defaultdict(list) # title -> list(urls)
    duplicate_descriptions = defaultdict(list) # description -> list(urls)
    missing_titles = [] # list(url)
    missing_descriptions = [] # list(url)
    short_descriptions = [] # list((url, desc_len))
    
    # Scanning
    for f in files:
        source_url = file_path_to_url(f)
        try:
            with open(f, 'r', encoding='utf-8') as file_obj:
                content = file_obj.read()
                
            parser = PageParser()
            parser.feed(content)
            
            # TDK Analysis
            # Exclude utility pages from TDK strict audit
            is_content_page = True
            if source_url in ['/404', '/sitemap', '/legal'] or source_url.startswith('/google'):
                is_content_page = False
            
            if is_content_page:
                if parser.page_title:
                    page_titles[source_url] = parser.page_title
                    duplicate_titles[parser.page_title].append(source_url)
                else:
                    missing_titles.append(source_url)
                    
                if parser.page_description:
                    page_descriptions[source_url] = parser.page_description
                    duplicate_descriptions[parser.page_description].append(source_url)
                    if len(parser.page_description) < 100:
                        short_descriptions.append((source_url, len(parser.page_description)))
                else:
                    missing_descriptions.append(source_url)
            
            for href, rel, text, classes in parser.links:
                # 1. Dirty Check
                is_dirty = False
                dirty_msg = href
                
                if href.endswith('.html') and not href.startswith(('http', '#', 'mailto')):
                     is_dirty = True
                elif '../' in href:
                     is_dirty = True
                elif not href.startswith('/') and not href.startswith(('http', '#', 'mailto', 'javascript:', 'tel:')):
                     is_dirty = True
                     dirty_msg = f"⚠️ Risky Relative Path: href=\"{href}\""
                
                if is_dirty:
                    dirty_links.append((os.path.basename(f), dirty_msg))
                
                # 2. Pyramid Model Check (Sales CTA Integrity)
                # Only check article pages (in /blog/)
                if '/blog/' in source_url:
                    is_sales_cta = False
                    # Check text keywords
                    keywords = ['立即开通', '购买', 'Get Started', 'Subscribe', '立即获取', '开通会员']
                    
                    # 1. Sidebar Sales Card Button (Specific Class)
                    if 'group/btn' in classes:
                         is_sales_cta = True
                    
                    # 2. Inline CTA Buttons (Style + Keywords)
                    # Usually bg-blue-600 or bg-gradient-to-r with white text
                    elif ('bg-blue-600' in classes or 'bg-gradient-to-r' in classes) and 'text-white' in classes:
                        if any(k in text for k in keywords):
                             is_sales_cta = True
                    
                    if is_sales_cta:
                        # Check destination
                        # Allowed: /#pricing, /#features, /, https://gemini-vip.top/#...
                        # We want to ensure it goes to homepage.
                        
                        # Normalize first
                        norm_href = href.strip()
                        
                        is_valid_dest = False
                        if norm_href == '/' or norm_href.startswith('/#') or norm_href.startswith('#'):
                            is_valid_dest = True
                        elif 'gemini-vip.top' in norm_href:
                             # absolute url to homepage
                             path = urlparse(norm_href).path
                             if path == '/' or path == '':
                                 is_valid_dest = True
                        
                        if not is_valid_dest:
                            pyramid_violations.append((source_url, text[:30], href))

                # 3. Build Graph
                
                # Check for External Links First
                if href.startswith(('http:', 'https:')) and 'gemini-vip.top' not in href:
                    try:
                        domain = urlparse(href).netloc
                        external_links[domain].append((source_url, rel))
                    except:
                        pass
                
                target_url = normalize_link(source_url, href)
                if target_url:
                    # Try to match target_url to a known page
                    # Exact match
                    matched_url = None
                    if target_url in url_to_file:
                        matched_url = target_url
                    # Try adding/removing slash
                    elif target_url + '/' in url_to_file:
                        matched_url = target_url + '/'
                    elif target_url.rstrip('/') in url_to_file:
                        matched_url = target_url.rstrip('/')
                    
                    if matched_url:
                        out_links[source_url].add(matched_url)
                        in_links[matched_url].add(source_url)
                    elif target_url in redirect_urls or target_url.rstrip('/') in redirect_urls:
                        # Valid redirect, treat as functional link
                        matched_redirect = target_url if target_url in redirect_urls else target_url.rstrip('/')
                        redirect_usage[matched_redirect].append((source_url, rel))
                    else:
                        # Check if it looks like an internal link that failed to match
                        # We already filtered external links in normalize_link
                        # So target_url is an absolute path like /foo/bar
                        # We should check if it's just an anchor or resource
                        if not target_url.endswith(('.png', '.jpg', '.css', '.js', '.xml', '.ico', '.svg')):
                             broken_links.append((source_url, target_url))

        except Exception as e:
            print(f"Error parsing {f}: {e}")

    print("\n" + "="*50)
    print("📊 DIAGNOSTIC REPORT")
    print("="*50)
    
    # 1. Orphan Pages
    print("\n🔴 Orphan Pages (In-links = 0):")
    orphans = []
    for url in url_to_file:
        if url == '/': continue
        if len(in_links[url]) == 0:
            orphans.append(url)
    
    if orphans:
        for url in sorted(orphans):
            print(f"  - {url}")
    else:
        print("  ✅ No orphan pages found.")

    # 2. Dirty URL Check
    print("\n⚠️ Dirty URL Check (Contains .html, ../, or Relative Path):")
    if dirty_links:
        for src, link in dirty_links:
            print(f"  - In {src}: {link}")
    else:
        print("  ✅ All internal links are clean.")

    # 3. Broken Link Check
    print("\n🔗 Broken Link Check (Internal 404s):")
    if broken_links:
        for src, target in broken_links:
             print(f"  - In {src} -> {target}")
    else:
        print("  ✅ No broken internal links found.")

    # 4. External Link Check
    print("\n🌐 External Link Check (Outbound):")
    if external_links:
        for domain, entries in sorted(external_links.items(), key=lambda x: len(x[1]), reverse=True):
            sources = [e[0] for e in entries]
            unique_sources = len(set(sources))
            print(f"  - {domain}: {len(sources)} links from {unique_sources} pages")
            
            # Check for rel attributes
            risky_links = []
            for src, rel in entries:
                is_risky = False
                if not rel:
                    is_risky = True
                
                # Report what's missing
                # Standard External Links: MUST have nofollow, noopener, noreferrer
                # Sponsored is optional (only for paid links), but if present, it's fine.
                required = {'nofollow', 'noopener', 'noreferrer'}
                current = set(rel.lower().split()) if rel else set()
                missing = required - current
                if missing:
                     risky_links.append((src, missing))

            if risky_links:
                 print(f"    ⚠️  Missing attributes in {len(risky_links)} links:")
                 # De-duplicate messages
                 shown_msgs = set()
                 for src, missing in risky_links:
                     msg = f"      In {src}: Missing {', '.join(sorted(missing))}"
                     if msg not in shown_msgs:
                         print(msg)
                         shown_msgs.add(msg)
            else:
                 print(f"    ✅ All links have full protection.")

            # Show example sources if not too many
            if unique_sources <= 3 and not risky_links:
                 print(f"    (from: {', '.join(sorted(list(set(sources))))})")
    else:
        print("  ✅ No external links found.")

    # 4.1 Redirect Usage Check (Link Equity Leakage)
    print("\n🔀 Internal Redirect Usage (Link Equity Leakage):")
    if redirect_usage:
        print(f"  Found {len(redirect_usage)} internal redirects being used.")
        redirect_risks = []
        
        for r_url, entries in sorted(redirect_usage.items()):
            print(f"  - {r_url} is linked from:")
            for src, rel in entries:
                print(f"    -> {src}")
                
                # Check for required attributes
                required_redirect = {'nofollow', 'sponsored', 'noopener', 'noreferrer'}
                current = set(rel.lower().split()) if rel else set()
                missing = required_redirect - current
                if missing:
                    redirect_risks.append((src, r_url, missing))

        if redirect_risks:
             print(f"\n  ⚠️  Missing attributes in {len(redirect_risks)} redirect links (MUST have sponsored):")
             for src, r_url, missing in redirect_risks:
                 print(f"    In {src} -> {r_url}: Missing {', '.join(sorted(missing))}")
        else:
             print("\n  ✅ All redirect links have strict 'nofollow sponsored noopener noreferrer' protection.")

    else:
        print("  ✅ No internal links point to redirects.")

    # 4.2 Pyramid Model Check
    print("\n🔺 Pyramid Model Check (Sales CTA Integrity):")
    if pyramid_violations:
        print(f"  ⚠️ Found {len(pyramid_violations)} Sales CTAs that do NOT point to Homepage Sales Card:")
        for src, txt, link in pyramid_violations:
            print(f"    - In {src}: \"{txt}\" -> {link}")
    else:
        print("  ✅ All Sales CTAs correctly point to Homepage Sales Card (Pyramid Model enforced).")


    # 5. Top Pages by In-links (Show ALL)
    print("\n📊 Page Connectivity Report (In-links Count):")
    sorted_pages = sorted(in_links.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Also include pages with 0 in-links that might not be in in_links dict if they have out-links
    all_known_pages = set(url_to_file.keys())
    pages_with_links = set(in_links.keys())
    for page in all_known_pages:
        if page not in pages_with_links:
            sorted_pages.append((page, set()))
            
    # Sort again to be safe
    sorted_pages.sort(key=lambda x: len(x[1]), reverse=True)

    for url, sources in sorted_pages:
        print(f"  - {url}: {len(sources)} incoming links")

    # 6. Click Depth (BFS)
    print("\n📉 Click Depth Analysis (Start: /):")
    depths = {url: float('inf') for url in url_to_file}
    depths['/'] = 0
    queue = deque(['/'])
    
    while queue:
        current_url = queue.popleft()
        current_depth = depths[current_url]
        
        for neighbor in out_links[current_url]:
            if neighbor in depths and depths[neighbor] == float('inf'):
                depths[neighbor] = current_depth + 1
                queue.append(neighbor)
    
    # Check for depth > 3
    deep_pages = []
    unreachable_pages = [] # Different from orphans? Orphans implies in-degree 0. Unreachable implies not reachable from Home.
    
    for url, d in depths.items():
        if d == float('inf'):
            unreachable_pages.append(url)
        elif d > 3:
            deep_pages.append((url, d))
            
    if deep_pages:
        print("  🔴 Warning: Pages with depth > 3:")
        for url, d in deep_pages:
            print(f"    - {url} (Depth: {d})")
    else:
        print("  ✅ All pages are within 3 clicks from Home.")
        
    if unreachable_pages:
         print(f"  ⚠️ {len(unreachable_pages)} pages are unreachable from Home (Depth: inf).")

    # 5. Sitemap Consistency Check
    print("\n🗺️ Sitemap Consistency Check:")
    scanned_urls = set(url_to_file.keys())
    
    # Files scanned but not in sitemap
    not_in_sitemap = scanned_urls - sitemap_urls
    # Filter out known non-sitemap pages
    not_in_sitemap = {u for u in not_in_sitemap if u not in ['/404']}
    
    if not_in_sitemap:
        print("  ⚠️ Files scanned but NOT in sitemap (Should they be included?):")
        for url in sorted(not_in_sitemap):
            print(f"    - {url}")
    else:
        print("  ✅ All scanned files are in sitemap.")
        
    # Files in sitemap but not scanned
    not_scanned = sitemap_urls - scanned_urls
    if not_scanned:
        print("  🔴 URLs in sitemap but NOT scanned (Missing files?):")
        for url in sorted(not_scanned):
            print(f"    - {url}")
    else:
        print("  ✅ All sitemap URLs exist on disk.")

    # 6. TDK Health Check
    print("\n📝 TDK Health Check (Titles & Descriptions):")
    
    # Process Duplicates
    real_dup_titles = {t: urls for t, urls in duplicate_titles.items() if len(urls) > 1}
    real_dup_descs = {d: urls for d, urls in duplicate_descriptions.items() if len(urls) > 1}
    
    has_tdk_issues = False
    
    if real_dup_titles:
        has_tdk_issues = True
        print(f"  🔴 Found {len(real_dup_titles)} sets of DUPLICATE Titles:")
        for title, urls in real_dup_titles.items():
            print(f"    - \"{title}\" used on {len(urls)} pages:")
            for u in sorted(urls)[:3]: # limit to 3 examples
                print(f"      * {u}")
            if len(urls) > 3: print(f"      * ... and {len(urls)-3} more")

    if real_dup_descs:
        has_tdk_issues = True
        print(f"  🔴 Found {len(real_dup_descs)} sets of DUPLICATE Descriptions:")
        for desc, urls in real_dup_descs.items():
            short_desc = (desc[:60] + '...') if len(desc) > 60 else desc
            print(f"    - \"{short_desc}\" used on {len(urls)} pages:")
            for u in sorted(urls)[:3]:
                print(f"      * {u}")
            if len(urls) > 3: print(f"      * ... and {len(urls)-3} more")

    if missing_titles:
        has_tdk_issues = True
        print(f"  ⚠️  Missing Titles on {len(missing_titles)} pages:")
        for u in sorted(missing_titles):
             print(f"    - {u}")

    if missing_descriptions:
        has_tdk_issues = True
        print(f"  ⚠️  Missing Descriptions on {len(missing_descriptions)} pages:")
        for u in sorted(missing_descriptions):
             print(f"    - {u}")

    if short_descriptions:
        has_tdk_issues = True
        print(f"  ⚠️  Short Descriptions (<100 chars) on {len(short_descriptions)} pages:")
        for u, l in sorted(short_descriptions):
             print(f"    - {u} ({l} chars)")

    if not has_tdk_issues:
        print("  ✅ TDK Health is perfect! No duplicates, missing, or short meta tags.")

    # 7. SEO Health Score
    print("\n" + "="*50)
    print("🏆 SEO HEALTH SCORE")
    print("="*50)

    score = 100
    deductions = []

    # Penalties
    # 1. Orphans (Exclude /404 and google verification files if desired, keeping it strict for now except 404)
    real_orphans = [u for u in orphans if u != '/404' and not u.startswith('/google')]
    if real_orphans:
        points = len(real_orphans) * 5
        score -= points
        deductions.append(f"-{points} pts: {len(real_orphans)} Orphan Pages (High Impact)")

    # 2. Dirty Links
    if dirty_links:
        points = len(dirty_links) * 1
        score -= points
        deductions.append(f"-{points} pts: {len(dirty_links)} Dirty URLs (Low Impact)")

    # 3. Broken Links
    if broken_links:
        points = len(broken_links) * 5
        score -= points
        deductions.append(f"-{points} pts: {len(broken_links)} Broken Links (High Impact)")
        
    # 4. Deep Pages
    if deep_pages:
        points = len(deep_pages) * 2
        score -= points
        deductions.append(f"-{points} pts: {len(deep_pages)} Deep Pages (>3 clicks) (Medium Impact)")

    # 5. Sitemap Inconsistency
    # Missing in Sitemap (Files exist but not in sitemap)
    # Exclude 404 and google verify
    real_not_in_sitemap = [u for u in not_in_sitemap if u != '/404' and not u.startswith('/google')]
    if real_not_in_sitemap:
        points = len(real_not_in_sitemap) * 2
        score -= points
        deductions.append(f"-{points} pts: {len(real_not_in_sitemap)} Files missing from Sitemap (Medium Impact)")
    
    # Missing Files (Sitemap has URL, Disk doesn't)
    if not_scanned:
        points = len(not_scanned) * 5
        score -= points
        deductions.append(f"-{points} pts: {len(not_scanned)} Sitemap URLs not found on disk (High Impact)")

    # 6. Pyramid Violations
    if pyramid_violations:
        points = len(pyramid_violations) * 5
        score -= points
        deductions.append(f"-{points} pts: {len(pyramid_violations)} Pyramid Model Violations (High Impact)")

    # 7. TDK Violations
    if real_dup_titles:
        # Heavy penalty for duplicate titles
        count = sum(len(urls) - 1 for urls in real_dup_titles.values()) # Count excess duplicates
        points = count * 10
        score -= points
        deductions.append(f"-{points} pts: {count} Duplicate Titles (Severe Impact)")

    if real_dup_descs:
        count = sum(len(urls) - 1 for urls in real_dup_descs.values())
        points = count * 5
        score -= points
        deductions.append(f"-{points} pts: {count} Duplicate Descriptions (High Impact)")
        
    if missing_titles:
        points = len(missing_titles) * 10
        score -= points
        deductions.append(f"-{points} pts: {len(missing_titles)} Missing Titles (Severe Impact)")

    if missing_descriptions:
        points = len(missing_descriptions) * 5
        score -= points
        deductions.append(f"-{points} pts: {len(missing_descriptions)} Missing Descriptions (Medium Impact)")
        
    if short_descriptions:
        points = len(short_descriptions) * 2
        score -= points
        deductions.append(f"-{points} pts: {len(short_descriptions)} Short Descriptions (Low Impact)")

    # Cap score
    score = max(0, score)
    
    # Grade
    if score >= 90: grade = "A 🌟"
    elif score >= 80: grade = "B ✅"
    elif score >= 70: grade = "C ⚠️"
    elif score >= 60: grade = "D 🔴"
    else: grade = "F 💀"

    print(f"\nFinal Score: {score}/100")
    print(f"Grade: {grade}")
    
    if deductions:
        print("\nDeductions:")
        for d in deductions:
            print(f"  {d}")
        print("\n💡 Tip: Fix 'High Impact' issues first to significantly improve your score.")
    else:
        print("\nPerfect Score! Great job! 🎉")
        
    print("\n" + "="*50)

if __name__ == '__main__':
    main()
