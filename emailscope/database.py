"""
Database module for EmailScope.
Handles data persistence using SQLite.
"""

import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

class EmailScopeDB:
    """Database manager for EmailScope."""
    
    def __init__(self, db_path: str = "emailscope.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()  # Thread safety lock
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create domains table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_scraped_at TIMESTAMP,
                    total_emails INTEGER DEFAULT 0,
                    verified_emails INTEGER DEFAULT 0
                )
            ''')
            
            # Create emails table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    is_valid BOOLEAN,
                    reason TEXT,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (domain_id) REFERENCES domains (id),
                    UNIQUE(domain_id, email)
                )
            ''')
            
            # Create scraping_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (domain_id) REFERENCES domains (id)
                )
            ''')
            
            # Create scraping_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_pages INTEGER DEFAULT 0,
                    total_emails_found INTEGER DEFAULT 0,
                    total_emails_verified INTEGER DEFAULT 0,
                    error_message TEXT,
                    FOREIGN KEY (domain_id) REFERENCES domains (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_domains_domain ON domains(domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_domain_id ON emails(domain_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_email ON emails(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_domain_id ON scraping_logs(domain_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_domain_id ON scraping_sessions(domain_id)')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def add_domain(self, domain: str, status: str = "pending") -> int:
        """
        Add a new domain to the database.
        
        Args:
            domain: Domain name
            status: Domain status (pending, scraping, completed, error)
            
        Returns:
            Domain ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO domains (domain, status, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (domain, status))
                domain_id = cursor.lastrowid
                conn.commit()
                self.logger.info(f"Added domain: {domain} (ID: {domain_id})")
                return domain_id
            except sqlite3.Error as e:
                self.logger.error(f"Error adding domain {domain}: {e}")
                raise
    
    def update_domain_status(self, domain: str, status: str, **kwargs):
        """
        Update domain status and metadata.
        
        Args:
            domain: Domain name
            status: New status
            **kwargs: Additional fields to update
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
            values = [status]
            
            for key, value in kwargs.items():
                if key in ['total_emails', 'verified_emails', 'last_scraped_at']:
                    update_fields.append(f"{key} = ?")
                    values.append(value)
            
            values.append(domain)
            
            cursor.execute(f'''
                UPDATE domains 
                SET {', '.join(update_fields)}
                WHERE domain = ?
            ''', values)
            
            conn.commit()
            self.logger.info(f"Updated domain {domain} status to {status}")
    
    def add_email(self, domain_id: int, email: str, confidence: int, 
                  is_valid: bool, reason: str, source: str) -> int:
        """
        Add an email to the database.
        
        Args:
            domain_id: Domain ID
            email: Email address
            confidence: Confidence score (0-100)
            is_valid: Whether email is valid
            reason: Verification reason
            source: How email was found (found, generated)
            
        Returns:
            Email ID
        """
        with self._lock:  # Thread safety
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO emails 
                        (domain_id, email, confidence, is_valid, reason, source)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (domain_id, email, confidence, is_valid, reason, source))
                    email_id = cursor.lastrowid
                    conn.commit()
                    self.logger.info(f"Added email: {email} (ID: {email_id})")
                    return email_id
                except sqlite3.Error as e:
                    self.logger.error(f"Error adding email {email}: {e}")
                    raise
    
    def add_log(self, domain_id: int, timestamp: str, message: str):
        """
        Add a log entry to the database.
        
        Args:
            domain_id: Domain ID
            timestamp: Log timestamp
            message: Log message
        """
        with self._lock:  # Thread safety
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO scraping_logs (domain_id, timestamp, message)
                    VALUES (?, ?, ?)
                ''', (domain_id, timestamp, message))
                conn.commit()
    
    def start_scraping_session(self, domain_id: int) -> int:
        """
        Start a new scraping session.
        
        Args:
            domain_id: Domain ID
            
        Returns:
            Session ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_sessions (domain_id, status)
                VALUES (?, 'started')
            ''', (domain_id,))
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
    
    def update_scraping_session(self, session_id: int, **kwargs):
        """
        Update scraping session.
        
        Args:
            session_id: Session ID
            **kwargs: Fields to update
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['status', 'total_pages', 'total_emails_found', 
                          'total_emails_verified', 'error_message', 'completed_at']:
                    update_fields.append(f"{key} = ?")
                    values.append(value)
            
            if update_fields:
                values.append(session_id)
                cursor.execute(f'''
                    UPDATE scraping_sessions 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                ''', values)
                conn.commit()
    
    def get_domain_by_name(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get domain by name."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM domains WHERE domain = ?', (domain,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_emails_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all emails for a domain."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, d.domain 
                FROM emails e 
                JOIN domains d ON e.domain_id = d.id 
                WHERE d.domain = ?
                ORDER BY e.created_at DESC
            ''', (domain,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_logs_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all logs for a domain."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT l.*, d.domain 
                FROM scraping_logs l 
                JOIN domains d ON l.domain_id = d.id 
                WHERE d.domain = ?
                ORDER BY l.created_at DESC
            ''', (domain,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_domains(self) -> List[Dict[str, Any]]:
        """Get all domains with statistics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT d.*, 
                       COUNT(e.id) as total_emails,
                       COUNT(CASE WHEN e.is_valid = 1 THEN 1 END) as verified_emails
                FROM domains d 
                LEFT JOIN emails e ON d.id = e.domain_id 
                GROUP BY d.id 
                ORDER BY d.updated_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scraping sessions."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, d.domain 
                FROM scraping_sessions s 
                JOIN domains d ON s.domain_id = d.id 
                ORDER BY s.started_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def export_domain_data(self, domain: str) -> Dict[str, Any]:
        """Export all data for a domain."""
        domain_data = self.get_domain_by_name(domain)
        if not domain_data:
            return None
        
        return {
            'domain': domain_data,
            'emails': self.get_emails_by_domain(domain),
            'logs': self.get_logs_by_domain(domain)
        }
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM scraping_logs 
                WHERE created_at < datetime('now', '-{} days')
            '''.format(days))
            deleted = cursor.rowcount
            conn.commit()
            self.logger.info(f"Cleaned up {deleted} old log entries")
            return deleted
