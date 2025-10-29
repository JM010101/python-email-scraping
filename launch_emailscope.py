#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EmailScope Launcher - Handles all startup issues
"""

import sys
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("EmailScope - Email Discovery & Verification System")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8+ required. Current version:", sys.version)
        return False
    
    # Add current directory to path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    try:
        # Import and run dashboard
        from emailscope.dashboard import dashboard
        
        print("Starting EmailScope Dashboard...")
        print("Dashboard URL: http://localhost:5000")
        print("Press Ctrl+C to stop")
        print("-" * 40)
        
        dashboard.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
        return True


    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nDashboard stopped. Goodbye!")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
