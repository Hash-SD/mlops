"""
Database Manager with support for PostgreSQL (Supabase) and SQLite.
Automatically detects database type from connection string.
"""

import time
import logging
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manager for database operations with retry logic and transaction support."""
    
    def __init__(self, db_url: str = "mlops_app.db"):
        self.db_url = db_url
        self.connection: Optional[Any] = None
        self.max_retries = 3
        self.retry_delay = 1
        self.is_postgres = self._is_postgresql()
        self._init_db_module()
    
    def _is_postgresql(self) -> bool:
        """Check if database URL is PostgreSQL."""
        return self.db_url.startswith('postgresql://') or self.db_url.startswith('postgres://')
    
    def _init_db_module(self):
        """Initialize appropriate database module."""
        if self.is_postgres:
            import psycopg2
            import psycopg2.extras
            self.db_module = psycopg2
            self.extras = psycopg2.extras
        else:
            import sqlite3
            self.db_module = sqlite3
            self.extras = None
    
    def connect(self) -> Any:
        """Establish database connection with retry logic."""
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                if self.is_postgres:
                    self.connection = self._connect_postgres()
                else:
                    self.connection = self._connect_sqlite()
                return self.connection
                
            except Exception as e:
                retries += 1
                last_error = e
                wait_time = self.retry_delay * (2 ** (retries - 1))
                logger.warning(f"Connection attempt {retries}/{self.max_retries} failed: {e}. Retrying in {wait_time}s...")
                if retries < self.max_retries:
                    time.sleep(wait_time)
        
        error_msg = f"Failed to connect after {self.max_retries} attempts: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def _connect_postgres(self) -> Any:
        """Connect to PostgreSQL database."""
        url = self.db_url
        if 'sslmode=' not in url:
            sep = '?' if '?' not in url else '&'
            url = f"{url}{sep}sslmode=require"
        
        try:
            conn = self.db_module.connect(url, cursor_factory=self.extras.RealDictCursor)
            conn.autocommit = False
            logger.info(f"PostgreSQL connection established")
            return conn
        except Exception as primary_error:
            # Try pooled connection as fallback
            if 'pooler.supabase.com' not in self.db_url and 'db.' in self.db_url and '.supabase.co' in self.db_url:
                pooled_url = self._build_pooled_url()
                if pooled_url:
                    logger.warning(f"Primary connect failed, trying pooled URL")
                    conn = self.db_module.connect(pooled_url, cursor_factory=self.extras.RealDictCursor)
                    conn.autocommit = False
                    logger.info("PostgreSQL pooled connection established")
                    return conn
            raise primary_error
    
    def _build_pooled_url(self) -> Optional[str]:
        """Build pooled connection URL for Supabase."""
        import re
        host_match = re.search(r"db\.([a-z0-9]+)\.supabase\.co", self.db_url)
        pwd_match = re.search(r"postgresql://[^:]+:([^@]+)@", self.db_url)
        
        if host_match and pwd_match:
            project_ref = host_match.group(1)
            password = pwd_match.group(1)
            return f"postgresql://postgres.{project_ref}:{password}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        return None
    
    def _connect_sqlite(self) -> Any:
        """Connect to SQLite database."""
        conn = self.db_module.connect(self.db_url, check_same_thread=False)
        conn.row_factory = self.db_module.Row
        logger.info(f"SQLite connection established: {self.db_url}")
        return conn
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
                self.connection = None
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def _convert_query_params(self, query: str, params: tuple) -> Tuple[str, tuple]:
        """Convert query parameters from ? (SQLite) to %s (PostgreSQL)."""
        if self.is_postgres and '?' in query:
            query = query.replace('?', '%s')
        return query, params
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query and return results."""
        try:
            if not self.connection:
                self.connect()
            
            query, params = self._convert_query_params(query, params)
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            cursor.close()
            
            logger.debug(f"Query executed: {query[:50]}... returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"Error executing query: {e}\nQuery: {query}\nParams: {params}")
            raise
    
    def execute_transaction(self, queries: List[Tuple[str, tuple]]) -> bool:
        """Execute multiple queries in single transaction."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            for query, params in queries:
                query, params = self._convert_query_params(query, params)
                cursor.execute(query, params)
            
            self.connection.commit()
            cursor.close()
            logger.info(f"Transaction completed: {len(queries)} queries executed")
            return True
            
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Transaction failed, rolled back: {e}")
            return False
    
    def insert_user_input(self, text: str, consent: bool) -> int:
        """Insert user input to database."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.is_postgres:
                query = "INSERT INTO users_inputs (text_input, user_consent, anonymized) VALUES (%s, %s, %s) RETURNING id"
                cursor.execute(query, (text, consent, False))
                input_id = cursor.fetchone()['id']
            else:
                query = "INSERT INTO users_inputs (text_input, user_consent, anonymized) VALUES (?, ?, ?)"
                cursor.execute(query, (text, consent, False))
                input_id = cursor.lastrowid
            
            self.connection.commit()
            cursor.close()
            logger.info(f"User input inserted: ID={input_id}, consent={consent}")
            return input_id
            
        except Exception as e:
            logger.error(f"Error inserting user input: {e}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def insert_prediction(self, input_id: int, model_version: str, prediction: str, confidence: float, latency: float) -> int:
        """Insert prediction result to database."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.is_postgres:
                query = "INSERT INTO predictions (input_id, model_version, prediction, confidence, latency) VALUES (%s, %s, %s, %s, %s) RETURNING id"
                cursor.execute(query, (input_id, model_version, prediction, confidence, latency))
                prediction_id = cursor.fetchone()['id']
            else:
                query = "INSERT INTO predictions (input_id, model_version, prediction, confidence, latency) VALUES (?, ?, ?, ?, ?)"
                cursor.execute(query, (input_id, model_version, prediction, confidence, latency))
                prediction_id = cursor.lastrowid
            
            self.connection.commit()
            cursor.close()
            logger.info(f"Prediction inserted: ID={prediction_id}, model={model_version}, confidence={confidence:.2f}")
            return prediction_id
            
        except Exception as e:
            logger.error(f"Error inserting prediction: {e}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def update_prediction_feedback(self, prediction_id: int, feedback_correct: bool) -> bool:
        """Update feedback for a prediction."""
        try:
            if not self.connection:
                self.connect()
            
            from datetime import datetime
            cursor = self.connection.cursor()
            
            if self.is_postgres:
                query = "UPDATE predictions SET feedback_correct = %s, feedback_timestamp = %s WHERE id = %s"
                cursor.execute(query, (feedback_correct, datetime.now(), prediction_id))
            else:
                query = "UPDATE predictions SET feedback_correct = ?, feedback_timestamp = ? WHERE id = ?"
                cursor.execute(query, (feedback_correct, datetime.now().isoformat(), prediction_id))
            
            self.connection.commit()
            cursor.close()
            logger.info(f"Feedback updated for prediction {prediction_id}: {feedback_correct}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating feedback: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics for monitoring."""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN feedback_correct IS NOT NULL THEN 1 ELSE 0 END) as with_feedback,
                    SUM(CASE WHEN feedback_correct = TRUE THEN 1 ELSE 0 END) as positive_feedback,
                    SUM(CASE WHEN feedback_correct = FALSE THEN 1 ELSE 0 END) as negative_feedback
                FROM predictions
            """
            
            if not self.is_postgres:
                query = query.replace('TRUE', '1').replace('FALSE', '0')
            
            results = self.execute_query(query)
            
            if results:
                row = results[0]
                return {
                    'total_predictions': row.get('total_predictions', 0) or 0,
                    'with_feedback': row.get('with_feedback', 0) or 0,
                    'positive_feedback': row.get('positive_feedback', 0) or 0,
                    'negative_feedback': row.get('negative_feedback', 0) or 0
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {}
    
    def get_training_data(self, train_ratio: float = 0.7) -> Dict[str, Any]:
        """Get data for training with specified train/test split ratio."""
        try:
            import random
            
            query = """
                SELECT p.id, u.text_input, p.prediction, p.feedback_correct, p.model_version
                FROM predictions p
                JOIN users_inputs u ON p.input_id = u.id
                WHERE p.feedback_correct IS NOT NULL AND u.user_consent = TRUE
            """
            
            if not self.is_postgres:
                query = query.replace('TRUE', '1')
            
            results = self.execute_query(query)
            
            valid_data = [
                {
                    'id': row['id'],
                    'text': row['text_input'],
                    'prediction': row['prediction'],
                    'feedback_correct': row['feedback_correct'],
                    'model_version': row['model_version']
                }
                for row in results
            ]
            
            random.shuffle(valid_data)
            split_idx = int(len(valid_data) * train_ratio)
            
            return {
                'train': valid_data[:split_idx],
                'test': valid_data[split_idx:],
                'stats': {
                    'total': len(valid_data),
                    'train_count': split_idx,
                    'test_count': len(valid_data) - split_idx,
                    'train_ratio': train_ratio
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return {'train': [], 'test': [], 'stats': {}}
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict]:
        """Get recent prediction logs from database."""
        try:
            placeholder = '%s' if self.is_postgres else '?'
            query = f"""
                SELECT p.id, p.timestamp, u.text_input, p.model_version, p.prediction, p.confidence, p.latency
                FROM predictions p
                JOIN users_inputs u ON p.input_id = u.id
                ORDER BY p.timestamp DESC
                LIMIT {placeholder}
            """
            return self.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error retrieving recent predictions: {e}")
            return []
    
    def get_dataset_snapshot(self, consent_only: bool = True) -> Any:
        """Get dataset snapshot for retraining."""
        try:
            import pandas as pd
            
            query = """
                SELECT u.id, u.timestamp, u.text_input, p.prediction, p.confidence, p.model_version
                FROM users_inputs u
                JOIN predictions p ON u.id = p.input_id
            """
            
            if consent_only:
                query += " WHERE u.user_consent = TRUE" if self.is_postgres else " WHERE u.user_consent = 1"
            
            query += " ORDER BY u.timestamp DESC"
            
            results = self.execute_query(query)
            df = pd.DataFrame(results)
            logger.info(f"Dataset snapshot: {len(df)} records, consent_only={consent_only}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving dataset snapshot: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_metrics_by_version(self) -> Dict[str, Dict]:
        """Get aggregated metrics per model version."""
        try:
            query = """
                SELECT model_version, COUNT(*) as prediction_count, AVG(confidence) as avg_confidence,
                       AVG(latency) as avg_latency, MIN(latency) as min_latency, MAX(latency) as max_latency
                FROM predictions
                GROUP BY model_version
                ORDER BY model_version
            """
            results = self.execute_query(query)
            
            metrics = {}
            for row in results:
                version = row['model_version']
                metrics[version] = {
                    'prediction_count': row['prediction_count'],
                    'avg_confidence': round(float(row['avg_confidence']), 4) if row['avg_confidence'] else 0,
                    'avg_latency': round(float(row['avg_latency']), 4) if row['avg_latency'] else 0,
                    'min_latency': round(float(row['min_latency']), 4) if row['min_latency'] else 0,
                    'max_latency': round(float(row['max_latency']), 4) if row['max_latency'] else 0
                }
            
            logger.debug(f"Metrics retrieved for {len(metrics)} model versions")
            return metrics
            
        except Exception as e:
            logger.error(f"Error retrieving metrics by version: {e}")
            return {}
    
    def initialize_schema(self, schema_file: str = None) -> bool:
        """Initialize database schema from SQL file."""
        try:
            if not self.connection:
                self.connect()
            
            if self._tables_exist():
                logger.info("Database tables already exist, skipping initialization")
                return True
            
            if schema_file is None:
                schema_file = "database/schema_postgres.sql" if self.is_postgres else "database/schema.sql"
            
            schema_path = Path(schema_file)
            if not schema_path.exists():
                logger.error(f"Schema file not found: {schema_file}")
                return False
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            cursor = self.connection.cursor()
            
            if self.is_postgres:
                statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                for statement in statements:
                    if statement:
                        cursor.execute(statement)
            else:
                cursor.executescript(schema_sql)
            
            self.connection.commit()
            cursor.close()
            logger.info("Database schema initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _tables_exist(self) -> bool:
        """Check if tables already exist."""
        try:
            if self.is_postgres:
                query = """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name IN ('users_inputs', 'predictions')
                """
            else:
                query = "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users_inputs', 'predictions')"
            
            results = self.execute_query(query)
            return len(results) == 2
            
        except Exception as e:
            logger.error(f"Error checking table existence: {e}")
            return False
    
    def migrate_schema(self, migration_sql: str) -> bool:
        """Execute database migration."""
        try:
            if not self.connection:
                self.connect()
            
            cursor = self.connection.cursor()
            
            if self.is_postgres:
                statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
                for statement in statements:
                    if statement:
                        cursor.execute(statement)
            else:
                cursor.executescript(migration_sql)
            
            self.connection.commit()
            cursor.close()
            logger.info("Database migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error executing database migration: {e}")
            if self.connection:
                self.connection.rollback()
            return False
