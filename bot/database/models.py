"""
Database models and schema definitions
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class Database:
    """Database manager for SQLite operations"""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection with row factory
        
        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self) -> None:
        """Initialize database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Complaints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mahalla TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Complaint images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS complaint_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complaint_id INTEGER NOT NULL,
                    channel_message_id INTEGER NOT NULL,
                    FOREIGN KEY (complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    # User operations
    def get_or_create_user(self, telegram_id: int, full_name: str) -> Dict[str, Any]:
        """
        Get existing user or create new one
        
        Args:
            telegram_id: User's Telegram ID
            full_name: User's full name
            
        Returns:
            Dict: User data
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Try to get existing user
            cursor.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            # Create new user
            cursor.execute(
                "INSERT INTO users (telegram_id, full_name) VALUES (?, ?)",
                (telegram_id, full_name)
            )
            conn.commit()
            
            cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (cursor.lastrowid,)
            )
            return dict(cursor.fetchone())
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by Telegram ID
        
        Args:
            telegram_id: User's Telegram ID
            
        Returns:
            Optional[Dict]: User data or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user_role(self, telegram_id: int, role: str) -> bool:
        """
        Update user role
        
        Args:
            telegram_id: User's Telegram ID
            role: New role (user/admin)
            
        Returns:
            bool: True if updated successfully
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET role = ? WHERE telegram_id = ?",
                (role, telegram_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # Complaint operations
    def create_complaint(
        self, 
        user_id: int, 
        mahalla: str, 
        category: str, 
        description: str
    ) -> int:
        """
        Create new complaint
        
        Args:
            user_id: User ID from users table
            mahalla: Mahalla name
            category: Complaint category
            description: Complaint description
            
        Returns:
            int: Created complaint ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO complaints (user_id, mahalla, category, description)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, mahalla, category, description)
            )
            conn.commit()
            return cursor.lastrowid
    
    def add_complaint_image(self, complaint_id: int, channel_message_id: int) -> int:
        """
        Add image to complaint
        
        Args:
            complaint_id: Complaint ID
            channel_message_id: Channel message ID
            
        Returns:
            int: Created image record ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO complaint_images (complaint_id, channel_message_id)
                VALUES (?, ?)
                """,
                (complaint_id, channel_message_id)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_complaint(self, complaint_id: int) -> Optional[Dict[str, Any]]:
        """
        Get complaint by ID
        
        Args:
            complaint_id: Complaint ID
            
        Returns:
            Optional[Dict]: Complaint data or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.*, u.full_name, u.telegram_id
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.id = ?
                """,
                (complaint_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_complaints(
        self, 
        user_id: int, 
        limit: int = 10, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get complaints for specific user
        
        Args:
            user_id: User ID from users table
            limit: Maximum number of complaints to return
            offset: Offset for pagination
            
        Returns:
            List[Dict]: List of complaints
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.*, u.full_name
                FROM complaints c
                JOIN users u ON c.user_id = u.id
                WHERE c.user_id = ?
                ORDER BY c.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_complaints(
        self, 
        limit: int = 10, 
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all complaints (for admin)
        
        Args:
            limit: Maximum number of complaints to return
            offset: Offset for pagination
            status: Filter by status
            
        Returns:
            List[Dict]: List of complaints
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute(
                    """
                    SELECT c.*, u.full_name, u.telegram_id
                    FROM complaints c
                    JOIN users u ON c.user_id = u.id
                    WHERE c.status = ?
                    ORDER BY c.created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (status, limit, offset)
                )
            else:
                cursor.execute(
                    """
                    SELECT c.*, u.full_name, u.telegram_id
                    FROM complaints c
                    JOIN users u ON c.user_id = u.id
                    ORDER BY c.created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset)
                )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_complaint_status(self, complaint_id: int, status: str) -> bool:
        """
        Update complaint status
        
        Args:
            complaint_id: Complaint ID
            status: New status
            
        Returns:
            bool: True if updated successfully
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE complaints SET status = ? WHERE id = ?",
                (status, complaint_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_complaint_images(self, complaint_id: int) -> List[int]:
        """
        Get channel message IDs for complaint images
        
        Args:
            complaint_id: Complaint ID
            
        Returns:
            List[int]: List of channel message IDs
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT channel_message_id FROM complaint_images WHERE complaint_id = ?",
                (complaint_id,)
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_complaint_count(self, user_id: Optional[int] = None) -> Dict[str, int]:
        """
        Get complaint statistics
        
        Args:
            user_id: Optional user ID to filter by user
            
        Returns:
            Dict: Complaint counts by status
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM complaints
                    WHERE user_id = ?
                    GROUP BY status
                    """,
                    (user_id,)
                )
            else:
                cursor.execute(
                    """
                    SELECT status, COUNT(*) as count
                    FROM complaints
                    GROUP BY status
                    """
                )
            
            result = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Ensure all statuses are present
            from bot.config import config
            for status in config.STATUSES.keys():
                if status not in result:
                    result[status] = 0
            
            return result
    
    def get_total_complaints(self) -> int:
        """
        Get total number of complaints
        
        Returns:
            int: Total complaints count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM complaints")
            return cursor.fetchone()[0]