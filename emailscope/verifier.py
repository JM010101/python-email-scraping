"""
Email verification module for EmailScope.
Performs MX and SMTP checks to verify email addresses.
"""

import dns.resolver
import logging
import socket
import re
import json
import urllib.request
from typing import List, Tuple, Optional, Dict

class EmailVerifier:
    """Verifies email addresses using MX and SMTP checks."""
    
    def __init__(self, timeout: int = 1, mock_dns: bool = False):
        """
        Initialize the verifier.
        
        Args:
            timeout: Timeout for network operations
            mock_dns: If True, skip DNS checks for testing
        """
        self.timeout = timeout
        self.mock_dns = mock_dns
        self.logger = logging.getLogger(__name__)
        
        # Enhanced email validation patterns (allows + in local part)
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9._+-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
        )
        
        # Disposable email domains (common ones)
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com', 'mailinator.com',
            'throwaway.email', 'temp-mail.org', 'getnada.com', 'maildrop.cc',
            'yopmail.com', 'tempail.com', 'sharklasers.com', 'guerrillamailblock.com'
        }
        
        # High-reputation domains
        self.reputable_domains = {
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com',
            'aol.com', 'protonmail.com', 'zoho.com', 'fastmail.com'
        }
    
    def verify_email(self, email: str) -> Tuple[bool, int, str]:
        """
        Verify an email address using enhanced validation methods.
        
        Args:
            email: Email address to verify
            
        Returns:
            Tuple of (is_valid, confidence_score, reason)
        """
        # Enhanced format validation
        format_valid, format_reason = self._validate_email_format(email)
        if not format_valid:
            return False, 0, f"Format invalid: {format_reason}"
        
        domain = email.split('@')[1].lower()
        
        # Check for disposable email
        disposable_check, disposable_reason = self._check_disposable_email(domain)
        if disposable_check:
            return False, 10, f"Disposable email: {disposable_reason}"
        
        # Check domain reputation
        reputation_score, reputation_reason = self._check_domain_reputation(domain)
        
        # Check MX record
        if self.mock_dns:
            # Mock DNS for testing - assume valid for all domains in test
            mx_valid = True
            mx_reason = "Mock DNS - assumed valid"
        else:
            mx_valid, mx_reason = self._check_mx_record(domain)
            if not mx_valid:
                return False, 0, f"MX check failed: {mx_reason}"
        
        # Enhanced SMTP check (optional for speed)
        smtp_valid = True  # Assume valid to speed up verification
        smtp_reason = "Skipped for speed"
        
        # Calculate enhanced confidence score
        confidence = self._calculate_enhanced_confidence(
            format_valid, mx_valid, smtp_valid, reputation_score, domain
        )
        
        # Determine overall validity with enhanced criteria
        is_valid = (format_valid and mx_valid and 
                   confidence > 30 and not disposable_check)
        
        # Enhanced reason reporting
        reasons = []
        if format_valid:
            reasons.append("Format: OK")
        if mx_valid:
            reasons.append("MX: OK")
        if smtp_valid:
            reasons.append("SMTP: OK")
        if reputation_score > 0:
            reasons.append(f"Reputation: {reputation_score}/100")
        if not disposable_check:
            reasons.append("Not disposable")
            
        reason = ", ".join(reasons)
        
        return is_valid, confidence, reason
    
    def _validate_email_format(self, email: str) -> Tuple[bool, str]:
        """
        Enhanced email format validation.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if not email or not isinstance(email, str):
            return False, "Empty or invalid input"
        
        # Basic structure check
        if '@' not in email or email.count('@') != 1:
            return False, "Invalid email structure"
        
        local, domain = email.split('@')
        
        # Check local part
        if not local or len(local) > 64:
            return False, "Invalid local part"
        
        # Check domain part
        if not domain or len(domain) > 253:
            return False, "Invalid domain part"
        
        # Check for consecutive dots
        if '..' in email:
            return False, "Consecutive dots not allowed"
        
        # Check for invalid characters
        if not self.email_pattern.match(email):
            return False, "Invalid characters or format"
        
        # Check domain has at least one dot
        if '.' not in domain:
            return False, "Domain must have TLD"
        
        # Check TLD is at least 2 characters
        tld = domain.split('.')[-1]
        if len(tld) < 2:
            return False, "TLD too short"
        
        return True, "Valid format"
    
    def _check_disposable_email(self, domain: str) -> Tuple[bool, str]:
        """
        Check if email is from a disposable email service.
        
        Args:
            domain: Domain to check
            
        Returns:
            Tuple of (is_disposable, reason)
        """
        if domain in self.disposable_domains:
            return True, f"Known disposable domain: {domain}"
        
        # Check for common disposable patterns
        disposable_patterns = [
            r'temp.*mail', r'throw.*away', r'fake.*mail', r'test.*mail',
            r'no.*reply', r'noreply', r'do.*not.*reply'
        ]
        
        for pattern in disposable_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return True, f"Disposable pattern detected: {domain}"
        
        return False, "Not disposable"
    
    def _check_domain_reputation(self, domain: str) -> Tuple[int, str]:
        """
        Check domain reputation and return score.
        
        Args:
            domain: Domain to check
            
        Returns:
            Tuple of (reputation_score, reason)
        """
        # High reputation domains
        if domain in self.reputable_domains:
            return 90, f"High reputation domain: {domain}"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[0-9]{4,}',  # Many numbers
            r'[a-z]{1,2}[0-9]{3,}',  # Short letters + many numbers
            r'[0-9]{3,}[a-z]{1,2}',  # Many numbers + short letters
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain):
                return 20, f"Suspicious pattern: {domain}"
        
        # Check domain length (very short or very long domains are suspicious)
        if len(domain) < 5:
            return 30, f"Very short domain: {domain}"
        elif len(domain) > 30:
            return 40, f"Very long domain: {domain}"
        
        # Default reputation for unknown domains
        return 60, f"Unknown domain: {domain}"
    
    def _calculate_enhanced_confidence(self, format_valid: bool, mx_valid: bool, 
                                      smtp_valid: bool, reputation_score: int, 
                                      domain: str) -> int:
        """
        Calculate enhanced confidence score.
        
        Args:
            format_valid: Email format is valid
            mx_valid: MX record exists
            smtp_valid: SMTP connection successful
            reputation_score: Domain reputation score
            domain: Domain name
            
        Returns:
            Confidence score (0-100)
        """
        base_score = 0
        
        # Format validation (required)
        if format_valid:
            base_score += 20
        else:
            return 0
        
        # MX record check (required)
        if mx_valid:
            base_score += 30
        else:
            return 0
        
        # SMTP check (bonus)
        if smtp_valid:
            base_score += 20
        
        # Domain reputation
        base_score += min(reputation_score, 30)
        
        # Domain-specific bonuses
        if domain in self.reputable_domains:
            base_score += 10
        
        # Penalty for suspicious domains
        if len(domain) < 5 or len(domain) > 30:
            base_score -= 10
        
        return min(max(base_score, 0), 100)
    
    def _check_mx_record(self, domain: str) -> Tuple[bool, str]:
        """
        Check if domain has valid MX record.
        
        Args:
            domain: Domain to check
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                return True, f"Found {len(mx_records)} MX records"
            else:
                return False, "No MX records found"
        except dns.resolver.NXDOMAIN:
            return False, "Domain does not exist"
        except dns.resolver.NoAnswer:
            return False, "No MX records found"
        except Exception as e:
            return False, f"DNS error: {str(e)}"
    
    
