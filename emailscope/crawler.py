"""
Web crawler module for EmailScope.
Handles respectful web scraping of company websites.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import List, Set, Optional
import re

class WebCrawler:
    """Advanced web crawler with intelligent page discovery and rate limiting."""
    
    def __init__(self, delay: float = 0.5, timeout: int = 10, bypass_robots: bool = True, 
                 max_depth: int = 2, max_pages: int = 50, rate_limit: float = 1.0):
        """
        Initialize the advanced crawler.
        
        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            bypass_robots: Whether to bypass robots.txt restrictions
            max_depth: Maximum crawling depth
            max_pages: Maximum pages to crawl
            rate_limit: Rate limiting factor (requests per second)
        """
        self.delay = delay
        self.timeout = timeout
        self.bypass_robots = bypass_robots
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.rate_limit = rate_limit
        self.session = requests.Session()
        
        # Enhanced headers with rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Crawling state
        self.visited_urls = set()
        self.crawled_urls = set()
        self.failed_urls = set()
        self.rate_limiter = time.time()
        
        self.logger = logging.getLogger(__name__)
        
    def crawl_company_website(self, domain: str) -> List[str]:
        """
        Advanced crawl a company website with intelligent page discovery.
        
        Args:
            domain: Company domain (e.g., 'example.com')
            
        Returns:
            List of URLs found on the website
        """
        # Reset crawling state
        self.visited_urls.clear()
        self.crawled_urls.clear()
        self.failed_urls.clear()
        
        # Ensure domain has protocol
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"
            
        try:
            print(f"[CRAWL] Starting advanced crawl for {domain}")
            
            # Check robots.txt first
            if not self._check_robots_txt(domain):
                self.logger.warning(f"Robots.txt disallows crawling for {domain}")
                print(f"[CRAWL] Robots.txt blocks crawling for {domain}")
                return []
            
            # Start with homepage
            urls_to_crawl = [domain]
            discovered_urls = set([domain])
            
            # Intelligent crawling with depth control
            for depth in range(self.max_depth + 1):
                if not urls_to_crawl or len(discovered_urls) >= self.max_pages:
                    break
                    
                print(f"[CRAWL] Depth {depth}: Processing {len(urls_to_crawl)} URLs")
                current_batch = urls_to_crawl.copy()
                urls_to_crawl.clear()
                
                for url in current_batch:
                    if len(discovered_urls) >= self.max_pages:
                        break
                        
                    if url in self.visited_urls:
                        continue
                        
                    # Rate limiting
                    self._apply_rate_limit()
                    
                    # Rotate user agent
                    self._rotate_user_agent()
                    
                    # Fetch page content
                    content = self._fetch_page(url)
                    if not content:
                        self.failed_urls.add(url)
                        continue
                        
                    self.visited_urls.add(url)
                    self.crawled_urls.add(url)
                    
                    # Extract links from current page
                    page_links = self._extract_links(content, domain)
                    
                    # Filter and prioritize links
                    filtered_links = self._filter_and_prioritize_links(page_links, domain)
                    
                    # Add new links for next depth
                    for link in filtered_links:
                        if link not in discovered_urls and len(discovered_urls) < self.max_pages:
                            discovered_urls.add(link)
                            if depth < self.max_depth:
                                urls_to_crawl.append(link)
                    
                    print(f"[CRAWL] Processed {url}: found {len(filtered_links)} new links")
            
            # Final URL list with prioritization
            final_urls = self._prioritize_urls(list(discovered_urls), domain)
            
            self.logger.info(f"Advanced crawl completed for {domain}: {len(final_urls)} pages")
            print(f"[CRAWL] Completed for {domain}: {len(final_urls)} pages, {len(self.failed_urls)} failed")
            return final_urls
            
        except Exception as e:
            self.logger.error(f"Error in advanced crawl for {domain}: {str(e)}")
            print(f"[CRAWL] Error crawling {domain}: {str(e)}")
            return []
    
    def _apply_rate_limit(self):
        """Apply rate limiting to prevent overwhelming servers."""
        current_time = time.time()
        time_since_last = current_time - self.rate_limiter
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)
            
        self.rate_limiter = time.time()
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection."""
        import random
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': user_agent})
    
    def _filter_and_prioritize_links(self, links: List[str], domain: str) -> List[str]:
        """Filter and prioritize links based on relevance."""
        filtered_links = []
        domain_parts = domain.replace('https://', '').replace('http://', '').split('/')[0]
        
        for link in links:
            # Skip if already visited or failed
            if link in self.visited_urls or link in self.failed_urls:
                continue
                
            # Must be from same domain
            if domain_parts not in link:
                continue
                
            # Skip common non-content URLs
            skip_patterns = [
                '/wp-admin/', '/admin/', '/login/', '/register/', '/signup/',
                '/logout/', '/api/', '/ajax/', '/static/', '/assets/', '/css/',
                '/js/', '/images/', '/img/', '/photos/', '/videos/', '/media/',
                '/download/', '/files/', '/documents/', '/pdf/', '/doc/',
                '/search/', '/filter/', '/sort/', '/page/', '/tag/', '/category/',
                '/archive/', '/feed/', '/rss/', '/sitemap', '/robots.txt',
                '/favicon.ico', '/apple-touch-icon', '/manifest.json'
            ]
            
            if any(pattern in link.lower() for pattern in skip_patterns):
                continue
                
            # Skip file extensions
            skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                             '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif',
                             '.svg', '.ico', '.css', '.js', '.xml', '.json', '.txt']
            
            if any(link.lower().endswith(ext) for ext in skip_extensions):
                continue
                
            filtered_links.append(link)
        
        # Prioritize by relevance
        return self._prioritize_links_by_relevance(filtered_links, domain)
    
    def _prioritize_links_by_relevance(self, links: List[str], domain: str) -> List[str]:
        """Prioritize links by relevance for email discovery."""
        priority_keywords = [
            'contact', 'about', 'team', 'staff', 'people', 'leadership', 'management',
            'support', 'help', 'info', 'news', 'press', 'media', 'company',
            'services', 'products', 'solutions', 'careers', 'jobs', 'hiring'
        ]
        
        def link_priority(link):
            score = 0
            link_lower = link.lower()
            
            # High priority for contact-related pages
            for keyword in priority_keywords:
                if keyword in link_lower:
                    score += 10
            
            # Medium priority for main sections
            if any(section in link_lower for section in ['/', '/home', '/index']):
                score += 5
                
            # Lower priority for deep paths
            path_depth = link.count('/') - 2  # Subtract domain slashes
            score -= path_depth
            
            return score
        
        return sorted(links, key=link_priority, reverse=True)
    
    def _prioritize_urls(self, urls: List[str], domain: str) -> List[str]:
        """Final prioritization of URLs for crawling."""
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        # Apply final prioritization
        prioritized = self._prioritize_links_by_relevance(unique_urls, domain)
        
        # Limit to max pages
        return prioritized[:self.max_pages]
    
    def _check_robots_txt(self, domain: str) -> bool:
        """Check if crawling is allowed by robots.txt."""
        if self.bypass_robots:
            # BYPASS ROBOTS.TXT - Always return True to ignore robots.txt
            # WARNING: This bypasses website crawling restrictions
            return True
        
        # Original robots.txt checking code:
        try:
            robots_url = urljoin(domain, '/robots.txt')
            response = self.session.get(robots_url, timeout=self.timeout)
            
            if response.status_code == 200:
                robots_content = response.text.lower()
                # Simple check - look for disallow patterns
                if 'disallow: /' in robots_content:
                    return False
            return True
        except:
            return True  # If we can't check, assume it's okay
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a single page and return BeautifulSoup object."""
        try:
            self.logger.debug(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Add delay between requests
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch {url}: {str(e)}")
            return None
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract relevant links from a page."""
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only include internal links
            if self._is_internal_link(full_url, base_url):
                # Clean URL (remove fragments and query params for email pages)
                clean_url = self._clean_url(full_url)
                links.add(clean_url)
        
        return links
    
    def _is_internal_link(self, url: str, base_url: str) -> bool:
        """Check if URL is internal to the domain."""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            return parsed_url.netloc == parsed_base.netloc
        except:
            return False
    
    def _clean_url(self, url: str) -> str:
        """Clean URL by removing fragments and unnecessary query params."""
        parsed = urlparse(url)
        # Remove fragment
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
        return clean_url
    
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get text content from a specific page."""
        soup = self._fetch_page(url)
        if soup:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text()
        return None
