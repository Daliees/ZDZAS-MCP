"""Database models for ZAS dashboard."""

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
import hashlib
import secrets
from contextlib import contextmanager


class Database:
    """SQLite database manager for ZAS dashboard."""
    
    def __init__(self, db_path: str = "zas_dashboard.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Activity logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    service TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Tool executions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    tool_name TEXT NOT NULL,
                    parameters TEXT,
                    result TEXT,
                    status TEXT DEFAULT 'success',
                    execution_time_ms INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    conversation_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    message_count INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    consensus_score REAL,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
                )
            """)
            
            # Create default admin user if not exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            if cursor.fetchone()[0] == 0:
                admin_password = self._hash_password("admin123")
                cursor.execute(
                    "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                    ("admin", admin_password)
                )
                print("✓ Created default admin user (username: admin, password: admin123)")
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt."""
        salt = "zas_salt_2025"  # In production, use random salt per user
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def create_user(self, username: str, password: str, email: Optional[str] = None, is_admin: bool = False) -> Optional[int]:
        """Create a new user."""
        try:
            password_hash = self._hash_password(password)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, ?)",
                    (username, password_hash, email, is_admin)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data."""
        password_hash = self._hash_password(password)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, email, is_admin, created_at FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            row = cursor.fetchone()
            if row:
                # Update last login
                cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), row['id']))
                return dict(row)
            return None
    
    def create_session(self, user_id: int, duration_hours: int = 24) -> str:
        """Create a session token for user."""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now().timestamp() + (duration_hours * 3600)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, datetime.fromtimestamp(expires_at))
            )
        
        return token
    
    def validate_session(self, token: str) -> Optional[Dict]:
        """Validate session token and return user data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.is_admin, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            """, (token,))
            
            row = cursor.fetchone()
            if row:
                expires_at = datetime.fromisoformat(row['expires_at'])
                if expires_at > datetime.now():
                    return dict(row)
                else:
                    # Delete expired session
                    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
            
            return None
    
    def delete_session(self, token: str):
        """Delete a session (logout)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_token = ?", (token,))
    
    def log_activity(self, user_id: Optional[int], action: str, service: Optional[str] = None, 
                    details: Optional[str] = None, ip_address: Optional[str] = None, 
                    user_agent: Optional[str] = None):
        """Log user activity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, service, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, action, service, details, ip_address, user_agent))
    
    def log_tool_execution(self, user_id: Optional[int], tool_name: str, parameters: str,
                          result: str, status: str = "success", execution_time_ms: Optional[int] = None):
        """Log tool execution."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tool_executions (user_id, tool_name, parameters, result, status, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, tool_name, parameters, result, status, execution_time_ms))
    
    def get_user_stats(self) -> List[Dict]:
        """Get usage statistics by user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    u.username,
                    COUNT(DISTINCT al.id) as activity_count,
                    COUNT(DISTINCT te.id) as tool_executions,
                    COUNT(DISTINCT c.id) as conversations,
                    MAX(al.timestamp) as last_activity
                FROM users u
                LEFT JOIN activity_logs al ON u.id = al.user_id
                LEFT JOIN tool_executions te ON u.id = te.user_id
                LEFT JOIN conversations c ON u.id = c.user_id
                GROUP BY u.id, u.username
                ORDER BY activity_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_tool_stats(self) -> List[Dict]:
        """Get tool usage statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    tool_name,
                    COUNT(*) as execution_count,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                    AVG(execution_time_ms) as avg_execution_time,
                    MAX(timestamp) as last_used
                FROM tool_executions
                GROUP BY tool_name
                ORDER BY execution_count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_activity(self, limit: int = 50) -> List[Dict]:
        """Get recent activity logs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    al.*,
                    u.username
                FROM activity_logs al
                LEFT JOIN users u ON al.user_id = u.id
                ORDER BY al.timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dashboard_stats(self) -> Dict:
        """Get overall dashboard statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']
            
            # Total activities
            cursor.execute("SELECT COUNT(*) as count FROM activity_logs")
            total_activities = cursor.fetchone()['count']
            
            # Total tool executions
            cursor.execute("SELECT COUNT(*) as count FROM tool_executions")
            total_executions = cursor.fetchone()['count']
            
            # Total conversations
            cursor.execute("SELECT COUNT(*) as count FROM conversations")
            total_conversations = cursor.fetchone()['count']
            
            # Activities today
            cursor.execute("""
                SELECT COUNT(*) as count FROM activity_logs 
                WHERE DATE(timestamp) = DATE('now')
            """)
            activities_today = cursor.fetchone()['count']
            
            return {
                "total_users": total_users,
                "total_activities": total_activities,
                "total_executions": total_executions,
                "total_conversations": total_conversations,
                "activities_today": activities_today,
            }


# Global database instance
_db: Optional[Database] = None


def get_database(db_path: str = "zas_dashboard.db") -> Database:
    """Get or create the global database instance."""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db
