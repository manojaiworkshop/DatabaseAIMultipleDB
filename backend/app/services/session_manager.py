"""
Session Manager for Multi-User Database Connections
Handles user sessions and their database connections
"""
import uuid
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import threading

logger = logging.getLogger(__name__)


class UserSession:
    """Represents a user session with database connection info"""
    
    def __init__(self, session_id: str, host: str, port: int, database: str,
                 username: str, password: str):
        self.session_id = session_id
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.request_count = 0
        
        # Cache for database snapshot
        self.schema_cache = None
        self.schema_cache_time = None
    
    def update_access(self):
        """Update last access time"""
        self.last_accessed = datetime.now()
        self.request_count += 1
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if session has expired"""
        elapsed = datetime.now() - self.last_accessed
        return elapsed > timedelta(minutes=timeout_minutes)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "database": self.database,
            "host": self.host,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "request_count": self.request_count
        }


class SessionManager:
    """
    Manages user sessions for multi-tenant database access
    Each user can connect to different databases
    """
    
    def __init__(self, session_timeout_minutes: int = 60):
        """
        Initialize session manager
        
        Args:
            session_timeout_minutes: Expire sessions after this many minutes of inactivity
        """
        self.sessions: Dict[str, UserSession] = {}
        self.session_timeout_minutes = session_timeout_minutes
        
        # Thread lock for session operations
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
        
        logger.info(f"SessionManager initialized (timeout={session_timeout_minutes}m)")
    
    def create_session(self, host: str, port: int, database: str,
                      username: str, password: str) -> str:
        """
        Create a new session for a user
        
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        with self.lock:
            session = UserSession(
                session_id=session_id,
                host=host,
                port=port,
                database=database,
                username=username,
                password=password
            )
            
            self.sessions[session_id] = session
            logger.info(f"Created session {session_id} for {database}@{host}")
            
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Get session by ID
        
        Returns:
            UserSession or None if not found/expired
        """
        with self.lock:
            if session_id not in self.sessions:
                logger.warning(f"Session {session_id} not found")
                return None
            
            session = self.sessions[session_id]
            
            # Check if expired
            if session.is_expired(self.session_timeout_minutes):
                logger.info(f"Session {session_id} expired")
                del self.sessions[session_id]
                return None
            
            # Update access time
            session.update_access()
            return session
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions.pop(session_id)
                logger.info(f"Deleted session {session_id} for {session.database}")
    
    def get_or_create_session(self, session_id: Optional[str],
                            host: str, port: int, database: str,
                            username: str, password: str) -> str:
        """
        Get existing session or create new one
        Useful for maintaining session across requests
        """
        # If session_id provided and valid, use it
        if session_id:
            session = self.get_session(session_id)
            if session:
                # Verify connection info matches
                if (session.host == host and 
                    session.port == port and 
                    session.database == database and
                    session.username == username):
                    return session_id
                else:
                    logger.warning(f"Session {session_id} connection mismatch, creating new")
        
        # Create new session
        return self.create_session(host, port, database, username, password)
    
    def _cleanup_expired_sessions(self):
        """Background thread to cleanup expired sessions"""
        import time
        
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes
                
                with self.lock:
                    expired_sessions = []
                    
                    for session_id, session in self.sessions.items():
                        if session.is_expired(self.session_timeout_minutes):
                            expired_sessions.append(session_id)
                    
                    # Remove expired sessions
                    for session_id in expired_sessions:
                        session = self.sessions.pop(session_id)
                        logger.info(f"Cleaned up expired session: {session_id} ({session.database})")
                    
                    if expired_sessions:
                        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions. Active: {len(self.sessions)}")
                        
            except Exception as e:
                logger.error(f"Error in session cleanup thread: {e}")
    
    def get_stats(self) -> Dict:
        """Get statistics about active sessions"""
        with self.lock:
            return {
                "total_sessions": len(self.sessions),
                "sessions": [
                    session.to_dict()
                    for session in self.sessions.values()
                ]
            }
    
    def clear_all(self):
        """Clear all sessions (for testing/shutdown)"""
        with self.lock:
            count = len(self.sessions)
            self.sessions.clear()
            logger.info(f"Cleared {count} sessions")


# Global session manager instance
session_manager = SessionManager(session_timeout_minutes=60)
