"""
Email extraction module for EmailScope.
Finds and extracts email addresses from web content.
"""

import re
import logging
from typing import List, Set, Optional, Tuple, Dict
from urllib.parse import urlparse

class EmailExtractor:
    """Advanced email extractor with intelligent discovery and pattern recognition."""
    
    def __init__(self):
        """Initialize the advanced email extractor."""
        self.logger = logging.getLogger(__name__)
        
        # Enhanced email regex patterns
        self.email_patterns = [
            # Standard email pattern
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            # Pattern for emails with spaces (common in HTML)
            re.compile(r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            # Pattern for emails in parentheses
            re.compile(r'\([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\)'),
            # Pattern for emails with "at" and "dot" obfuscation
            re.compile(r'\b[A-Za-z0-9._%+-]+\s+at\s+[A-Za-z0-9.-]+\s+dot\s+[A-Z|a-z]{2,}\b', re.I),
            # Pattern for emails with [at] and [dot] obfuscation
            re.compile(r'\b[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Z|a-z]{2,}\b', re.I)
        ]
        
        # Advanced common email formats with context
        self.common_formats = [
            'info@{domain}',
            'contact@{domain}',
            'hello@{domain}',
            'support@{domain}',
            'sales@{domain}',
            'admin@{domain}',
            'team@{domain}',
            'office@{domain}',
            'help@{domain}',
            'service@{domain}',
            'inquiry@{domain}',
            'general@{domain}',
            'main@{domain}',
            'primary@{domain}'
        ]
        
        # Industry-specific email patterns
        self.industry_patterns = {
            'tech': ['dev@{domain}', 'tech@{domain}', 'engineering@{domain}', 'developers@{domain}'],
            'media': ['press@{domain}', 'media@{domain}', 'news@{domain}', 'editor@{domain}'],
            'finance': ['finance@{domain}', 'accounting@{domain}', 'billing@{domain}', 'payments@{domain}'],
            'healthcare': ['medical@{domain}', 'health@{domain}', 'patient@{domain}', 'clinic@{domain}'],
            'education': ['academic@{domain}', 'education@{domain}', 'student@{domain}', 'faculty@{domain}'],
            'retail': ['store@{domain}', 'shop@{domain}', 'orders@{domain}', 'customers@{domain}']
        }
        
        # Email context keywords for better discovery
        self.email_context_keywords = [
            'email', 'contact', 'reach', 'get in touch', 'write to', 'send to',
            'mail', 'message', 'inquiry', 'question', 'support', 'help'
        ]
    
    def extract_emails_from_content(self, content: str) -> Set[str]:
        """
        Advanced email extraction with multiple patterns and obfuscation handling.
        
        Args:
            content: Text content to search
            
        Returns:
            Set of found email addresses
        """
        emails = set()
        
        if not content:
            return emails
        
        # Try all email patterns
        for pattern in self.email_patterns:
            matches = pattern.findall(content)
            for email in matches:
                # Clean and normalize email
                clean_email = self._normalize_email(email)
                if clean_email and self._is_valid_email(clean_email):
                    emails.add(clean_email)
        
        # Handle obfuscated emails
        obfuscated_emails = self._extract_obfuscated_emails(content)
        emails.update(obfuscated_emails)
        
        # Extract emails from context
        context_emails = self._extract_emails_from_context(content)
        emails.update(context_emails)
        
        self.logger.debug(f"Extracted {len(emails)} emails from content")
        return emails
    
    def _normalize_email(self, email: str) -> str:
        """Normalize email address by cleaning spaces and special characters."""
        if not email:
            return ""
        
        # Remove parentheses
        email = email.strip('()')
        
        # Clean spaces around @ symbol
        email = re.sub(r'\s*@\s*', '@', email)
        
        # Clean spaces around dots
        email = re.sub(r'\s*\.\s*', '.', email)
        
        # Remove extra spaces
        email = email.strip()
        
        return email.lower()
    
    def _extract_obfuscated_emails(self, content: str) -> Set[str]:
        """Extract emails that are obfuscated with 'at' and 'dot'."""
        emails = set()
        
        # Pattern for "user at domain dot com" format
        at_dot_pattern = re.compile(r'\b([A-Za-z0-9._%+-]+)\s+at\s+([A-Za-z0-9.-]+)\s+dot\s+([A-Z|a-z]{2,})\b', re.I)
        matches = at_dot_pattern.findall(content)
        
        for user, domain, tld in matches:
            email = f"{user}@{domain}.{tld}"
            if self._is_valid_email(email):
                emails.add(email.lower())
        
        # Pattern for "user[at]domain[dot]com" format
        bracket_pattern = re.compile(r'\b([A-Za-z0-9._%+-]+)\s*\[at\]\s*([A-Za-z0-9.-]+)\s*\[dot\]\s*([A-Z|a-z]{2,})\b', re.I)
        matches = bracket_pattern.findall(content)
        
        for user, domain, tld in matches:
            email = f"{user}@{domain}.{tld}"
            if self._is_valid_email(email):
                emails.add(email.lower())
        
        return emails
    
    def _extract_emails_from_context(self, content: str) -> Set[str]:
        """Extract emails based on surrounding context."""
        emails = set()
        
        # Look for email patterns near context keywords
        for keyword in self.email_context_keywords:
            # Find context around keywords
            context_pattern = re.compile(
                rf'(?:{re.escape(keyword)}[^@]*?)([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{{2,}})',
                re.I
            )
            matches = context_pattern.findall(content)
            
            for email in matches:
                clean_email = self._normalize_email(email)
                if clean_email and self._is_valid_email(clean_email):
                    emails.add(clean_email)
        
        return emails
    
    def extract_emails_from_links(self, soup) -> Set[str]:
        """
        Extract emails from mailto links.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Set of found email addresses
        """
        emails = set()
        
        if not soup:
            return emails
        
        # Find mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        
        for link in mailto_links:
            href = link.get('href', '')
            if href.startswith('mailto:'):
                email = href[7:]  # Remove 'mailto:' prefix
                # Remove query parameters
                email = email.split('?')[0]
                clean_email = email.strip().lower()
                if self._is_valid_email(clean_email):
                    emails.add(clean_email)
        
        self.logger.debug(f"Extracted {len(emails)} emails from mailto links")
        return emails
    
    def generate_common_emails(self, domain: str) -> List[str]:
        """
        Generate intelligent email formats for a domain.
        
        Args:
            domain: Domain name (e.g., 'example.com')
            
        Returns:
            List of generated email addresses
        """
        emails = []
        
        # Clean domain
        clean_domain = domain.lower().strip()
        if clean_domain.startswith('www.'):
            clean_domain = clean_domain[4:]
        
        # Generate standard common emails
        for format_template in self.common_formats:
            email = format_template.format(domain=clean_domain)
            emails.append(email)
        
        # Generate industry-specific emails
        industry_emails = self._generate_industry_emails(clean_domain)
        emails.extend(industry_emails)
        
        # Generate company-specific emails
        company_emails = self._generate_company_emails(clean_domain)
        emails.extend(company_emails)
        
        return emails
    
    def _generate_industry_emails(self, domain: str) -> List[str]:
        """Generate industry-specific email patterns."""
        emails = []
        domain_lower = domain.lower()
        
        # Detect industry based on domain keywords
        industry = self._detect_industry(domain_lower)
        
        if industry in self.industry_patterns:
            for pattern in self.industry_patterns[industry]:
                email = pattern.format(domain=domain)
                emails.append(email)
        
        return emails
    
    def _detect_industry(self, domain: str) -> str:
        """Detect industry based on domain name and keywords."""
        tech_keywords = ['tech', 'software', 'app', 'dev', 'code', 'digital', 'it', 'computer']
        media_keywords = ['media', 'news', 'press', 'blog', 'content', 'publishing']
        finance_keywords = ['bank', 'finance', 'financial', 'investment', 'capital', 'money']
        healthcare_keywords = ['health', 'medical', 'clinic', 'hospital', 'doctor', 'care']
        education_keywords = ['edu', 'university', 'college', 'school', 'academy', 'institute']
        retail_keywords = ['shop', 'store', 'market', 'commerce', 'retail', 'buy']
        
        if any(keyword in domain for keyword in tech_keywords):
            return 'tech'
        elif any(keyword in domain for keyword in media_keywords):
            return 'media'
        elif any(keyword in domain for keyword in finance_keywords):
            return 'finance'
        elif any(keyword in domain for keyword in healthcare_keywords):
            return 'healthcare'
        elif any(keyword in domain for keyword in education_keywords):
            return 'education'
        elif any(keyword in domain for keyword in retail_keywords):
            return 'retail'
        
        return 'general'
    
    def _generate_company_emails(self, domain: str) -> List[str]:
        """Generate company-specific email patterns."""
        emails = []
        
        # Extract company name from domain
        company_name = domain.split('.')[0]
        
        # Generate emails based on company name
        company_emails = [
            f"{company_name}@{domain}",
            f"info@{company_name}.com",
            f"contact@{company_name}.com",
            f"hello@{company_name}.com"
        ]
        
        # Add company-specific patterns
        if len(company_name) > 3:
            # Shortened company name
            short_name = company_name[:3]
            emails.extend([
                f"{short_name}@{domain}",
                f"info@{short_name}.com"
            ])
        
        return company_emails
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email appears valid
        """
        if not email or '@' not in email:
            return False
        
        # Basic validation
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        
        # Check local part
        if not local or len(local) > 64:
            return False
        
        # Check domain part
        if not domain or len(domain) > 255:
            return False
        
        # Check for valid characters
        if not re.match(r'^[A-Za-z0-9._%+-]+$', local):
            return False
        
        if not re.match(r'^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', domain):
            return False
        
        return True
    
    def extract_all_emails(self, content: str, soup=None, domain: str = None) -> Tuple[Set[str], Set[str], Dict[str, str]]:
        """
        Extract all emails from content and links with source tracking.
        
        Args:
            content: Text content
            soup: BeautifulSoup object (optional)
            domain: Domain for generating common emails (optional)
            
        Returns:
            Tuple of (found_emails, generated_emails, email_sources)
        """
        found_emails = set()
        generated_emails = set()
        email_sources = {}
        
        # Extract from content
        content_emails = self.extract_emails_from_content(content)
        found_emails.update(content_emails)
        for email in content_emails:
            email_sources[email] = "found"
        
        # Extract from links
        if soup:
            link_emails = self.extract_emails_from_links(soup)
            found_emails.update(link_emails)
            for email in link_emails:
                email_sources[email] = "mailto_link"
        
        # Generate common emails if domain provided
        if domain:
            generated_emails_list = self.generate_common_emails(domain)
            generated_emails.update(generated_emails_list)
            for email in generated_emails_list:
                email_sources[email] = "generated"
        
        return found_emails, generated_emails, email_sources
    
    def get_email_confidence_score(self, email: str, source: str, domain: str) -> int:
        """
        Calculate confidence score for an email based on source and context.
        
        Args:
            email: Email address
            source: Source of the email (found, mailto_link, generated)
            domain: Domain name
            
        Returns:
            Confidence score (0-100)
        """
        base_score = 0
        
        # Source-based scoring
        if source == "mailto_link":
            base_score = 90  # Highest confidence for mailto links
        elif source == "found":
            base_score = 70  # Good confidence for found emails
        elif source == "generated":
            base_score = 30  # Lower confidence for generated emails
        
        # Domain matching bonus
        email_domain = email.split('@')[1] if '@' in email else ''
        if email_domain.lower() == domain.lower():
            base_score += 10
        
        # Common email patterns bonus
        common_patterns = ['info', 'contact', 'hello', 'support', 'sales', 'admin']
        email_local = email.split('@')[0] if '@' in email else ''
        if any(pattern in email_local.lower() for pattern in common_patterns):
            base_score += 5
        
        return min(base_score, 100)
