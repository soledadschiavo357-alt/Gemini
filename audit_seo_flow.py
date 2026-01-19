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

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.links.append(value)

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

    # Graph Data
    out_links = defaultdict(set) # url -> set(target_urls)
    in_links = defaultdict(set)  # url -> set(source_urls)
    dirty_links = [] # (source_file, link)
    broken_links = [] # (source_url, target_url)
    external_links = defaultdict(list) # target_domain -> list(source_urls)
    
    # Scanning
    for f in files:
        source_url = file_path_to_url(f)
        try:
            with open(f, 'r', encoding='utf-8') as file_obj:
                content = file_obj.read()
                
            parser = LinkExtractor()
            parser.feed(content)
            
            for href in parser.links:
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
                
                # 2. Build Graph
                
                # Check for External Links First
                if href.startswith(('http:', 'https:')) and 'gemini-vip.top' not in href:
                    try:
                        domain = urlparse(href).netloc
                        external_links[domain].append(source_url)
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
        for domain, sources in sorted(external_links.items(), key=lambda x: len(x[1]), reverse=True):
            unique_sources = len(set(sources))
            print(f"  - {domain}: {len(sources)} links from {unique_sources} pages")
            # Show example sources if not too many
            if unique_sources <= 3:
                 print(f"    (from: {', '.join(sorted(list(set(sources))))})")
    else:
        print("  ✅ No external links found.")

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

if __name__ == '__main__':
    main()
