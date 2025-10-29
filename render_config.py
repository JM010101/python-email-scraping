#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Free Render Optimized Configuration for EmailScope
Designed specifically for Render's free tier limitations
"""

import os
import sys
import platform
from pathlib import Path

def create_wsgi_app():
    """Create WSGI application optimized for free Render deployment."""
    
    # Add current directory to path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    try:
        from emailscope.dashboard import EmailScopeDashboard
        
        # Get configuration optimized for FREE Render tier
        config = get_free_render_config()
        
        print("🚀 Starting EmailScope - FREE RENDER OPTIMIZED")
        print("=" * 60)
        print(f"Platform: {platform.system()} {platform.release()}")
        print("⚠️  FREE TIER LIMITATIONS:")
        print("   - 30 second process timeout")
        print("   - 512MB memory limit")
        print("   - Shared CPU resources")
        print("   - Limited network connections")
        print("-" * 60)
        print(f"Configuration: {config}")
        print("-" * 60)
        
        # Create dashboard with free-tier optimized settings
        dashboard = EmailScopeDashboard(config)
        
        # Return the Flask app for WSGI
        return dashboard.app
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        raise
    except Exception as e:
        print(f"Error creating WSGI app: {e}")
        raise

def get_free_render_config():
    """Get configuration optimized for Render deployment."""
    
    # Check if running on Render
    is_render = os.environ.get('RENDER', False) or os.environ.get('PORT', False)
    
    if is_render:
        print("🌐 Render deployment detected")
        return {
            # Optimized settings for paid Render tier
            'delay': 1.0,           # Faster delay for paid tier
            'timeout': 30,           # Longer timeout for paid tier
            'bypass_robots': False,  # Respect robots.txt for paid tier
            'max_depth': 2,          # Deeper crawling for paid tier
            'max_pages': 20,         # More pages for paid tier
            'rate_limit': 1.0,       # Faster rate for paid tier
            
            # Email verification settings
            'verification_timeout': 5,   # Standard DNS timeout
            'mock_dns': False,           # Real DNS verification for paid tier
            
            # Process management
            'max_workers': 3,        # Multiple workers for paid tier
            'request_retries': 3,    # Standard retries
            
            # Paid tier specific settings
            'max_emails_per_page': 50,   # More emails per page
            'max_total_emails': 200,     # More total emails
            'enable_timeout_protection': False,  # No timeout protection needed
        }
    else:
        print("💻 Local development mode")
        return {
            # Local settings (faster than free Render)
            'delay': 1.0,
            'timeout': 20,
            'bypass_robots': False,
            'max_depth': 2,
            'max_pages': 15,
            'rate_limit': 1.5,
            'verification_timeout': 3,
            'mock_dns': False,
            'max_workers': 3,
            'request_retries': 3,
            'max_emails_per_page': 50,
            'max_total_emails': 100,
            'enable_timeout_protection': False,
        }

# WSGI application entry point
application = create_wsgi_app()

if __name__ == '__main__':
    # This should not be called directly in production
    print("⚠️  This is a WSGI application optimized for FREE Render.")
    print("   Use Waitress (Windows) or Gunicorn (Unix) to run it.")
    print("   Windows: waitress-serve --host=0.0.0.0 --port=5000 render_config:application")
    print("   Unix: gunicorn -w 1 -b 0.0.0.0:5000 render_config:application")