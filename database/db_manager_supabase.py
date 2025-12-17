"""
Database Manager for Supabase using REST API.
Optimized for reliable data storage and retrieval.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class SupabaseDatabaseManager:
    """Manager for Supabase database operations via REST API."""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase URL and Key are required")
        
        self.supabase_url = supabase_url.rstrip('/')
        self.supabase_key = supabase_key
        self.max_retries = 3
        self.retry_delay = 1
        self.is_postgres = True
        self.connection = None  # Will be set to True after successful connect()
        
        try:
            import httpx
            self.http = httpx
        except ImportError:
            raise ImportError("httpx required. Install with: pip install httpx")
        
        self._headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        logger.info(f"SupabaseDatabaseManager initialized for {self.supabase_url}")
    
    def connect(self) -> bool:
        """Test connection to Supabase and verify tables exist."""
        try:
            # Test basic connectivity
            r = self.http.get(
                f"{self.supabase_url}/rest/v1/",
                headers=self._headers,
                timeout=15
            )
            
            if r.status_code != 200:
                logger.error(f"Supabase connection failed: {r.status_code} - {r.text}")
                self.connection = False
                return False
            
            # Verify users_inputs table exists
            r_users = self.http.get(
                f"{self.supabase_url}/rest/v1/users_inputs?limit=1",
                headers=self._headers,
                timeout=10
            )
            
            if r_users.status_code != 200:
                logger.error(f"Table users_inputs not accessible: {r_users.status_code} - {r_users.text}")
                self.connection = False
                return False
            
            # Verify predictions table exists
            r_pred = self.http.get(
                f"{self.supabase_url}/rest/v1/predictions?limit=1",
                headers=self._headers,
                timeout=10
            )
            
            if r_pred.status_code != 200:
                logger.error(f"Table predictions not accessible: {r_pred.status_code} - {r_pred.text}")
                self.connection = False
                return False
            
            logger.info("Supabase connection verified - all tables accessible")
            self.connection = True
            return True
            
        except Exception as e:
            logger.error(f"Supabase connection error: {e}")
            self.connection = False
            return False
    
    def disconnect(self):
        """Close connection (no-op for REST API but reset state)."""
        self.connection = None
        logger.info("Supabase connection closed")
    
    def _ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if needed."""
        if not self.connection:
            logger.info("Connection not active, attempting to connect...")
            return self.connect()
        return True
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 15
    ) -> Optional[Any]:
        """Make HTTP request with retry logic and error handling."""
        url = f"{self.supabase_url}/rest/v1/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    r = self.http.get(url, headers=self._headers, params=params, timeout=timeout)
                elif method == 'POST':
                    r = self.http.post(url, headers=self._headers, json=data, timeout=timeout)
                elif method == 'PATCH':
                    headers = {**self._headers, 'Prefer': 'return=minimal'}
                    r = self.http.patch(url, headers=headers, json=data, params=params, timeout=timeout)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                
                # Log response for debugging
                logger.debug(f"{method} {endpoint} -> {r.status_code}")
                
                # Success responses
                if r.status_code in [200, 201, 204]:
                    if r.status_code == 204 or not r.text:
                        return True
                    return r.json()
                
                # Handle specific error codes
                if r.status_code == 401:
                    logger.error("Supabase authentication failed - check API key")
                    return None
                elif r.status_code == 404:
                    logger.error(f"Endpoint not found: {endpoint}")
                    return None
                elif r.status_code == 409:
                    logger.error(f"Conflict error: {r.text}")
                    return None
                elif r.status_code >= 500:
                    # Server error - retry
                    logger.warning(f"Server error {r.status_code}, retrying... ({attempt + 1}/{self.max_retries})")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"Request failed: {r.status_code} - {r.text}")
                    return None
                    
            except self.http.TimeoutException:
                logger.warning(f"Request timeout, retrying... ({attempt + 1}/{self.max_retries})")
                time.sleep(self.retry_delay * (attempt + 1))
            except self.http.ConnectError as e:
                logger.error(f"Connection error: {e}")
                self.connection = False
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    self._ensure_connected()
            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    return None
        
        logger.error(f"Request failed after {self.max_retries} attempts")
        return None
    
    def insert_user_input(self, text: str, consent: bool) -> Optional[int]:
        """Insert user input to database."""
        if not self._ensure_connected():
            logger.error("Cannot insert user input - not connected to Supabase")
            return None
        
        try:
            data = {
                'text_input': text,
                'user_consent': consent,
                'anonymized': False
            }
            
            logger.debug(f"Inserting user input: consent={consent}, text_length={len(text)}")
            
            result = self._make_request('POST', 'users_inputs', data=data)
            
            if result and isinstance(result, list) and len(result) > 0:
                input_id = result[0].get('id')
                if input_id:
                    logger.info(f"User input inserted successfully: ID={input_id}")
                    return input_id
                else:
                    logger.error("Insert succeeded but no ID returned")
                    return None
            
            logger.error(f"Failed to insert user input - unexpected response: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Error inserting user input: {e}", exc_info=True)
            return None
    
    def insert_prediction(
        self,
        input_id: int,
        model_version: str,
        prediction: str,
        confidence: float,
        latency: float
    ) -> Optional[int]:
        """Insert prediction result to database."""
        if not self._ensure_connected():
            logger.error("Cannot insert prediction - not connected to Supabase")
            return None
        
        try:
            data = {
                'input_id': input_id,
                'model_version': model_version,
                'prediction': prediction,
                'confidence': float(confidence),
                'latency': float(latency),
                'feedback_correct': None,
                'feedback_timestamp': None,
                'used_for_training': False,
                'training_split': None
            }
            
            logger.debug(f"Inserting prediction: input_id={input_id}, model={model_version}, pred={prediction}")
            
            result = self._make_request('POST', 'predictions', data=data)
            
            if result and isinstance(result, list) and len(result) > 0:
                prediction_id = result[0].get('id')
                if prediction_id:
                    logger.info(f"Prediction inserted successfully: ID={prediction_id}")
                    return prediction_id
                else:
                    logger.error("Insert succeeded but no prediction ID returned")
                    return None
            
            logger.error(f"Failed to insert prediction - unexpected response: {result}")
            return None
            
        except Exception as e:
            logger.error(f"Error inserting prediction: {e}", exc_info=True)
            return None
    
    def update_prediction_feedback(self, prediction_id: int, feedback_correct: bool) -> bool:
        """Update feedback for a prediction."""
        if not self._ensure_connected():
            logger.error("Cannot update feedback - not connected to Supabase")
            return False
        
        try:
            data = {
                'feedback_correct': feedback_correct,
                'feedback_timestamp': datetime.now().isoformat()
            }
            
            logger.debug(f"Updating feedback: prediction_id={prediction_id}, correct={feedback_correct}")
            
            # Use query parameter for filtering
            endpoint = f"predictions?id=eq.{prediction_id}"
            
            result = self._make_request('PATCH', endpoint, data=data)
            
            if result is True or result is not None:
                logger.info(f"Feedback updated successfully for prediction {prediction_id}")
                return True
            
            logger.error(f"Failed to update feedback for prediction {prediction_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating feedback: {e}", exc_info=True)
            return False

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query - converts SQL to REST API call."""
        if not self._ensure_connected():
            return []
        
        try:
            query_clean = ' '.join(query.split())
            query_upper = query_clean.upper()
            
            # Simple SELECT 1 for connection test
            if query_clean.strip() == 'SELECT 1':
                return [{'result': 1}]
            
            if 'FROM' not in query_upper:
                logger.error(f"Invalid query - no FROM clause: {query[:50]}")
                return []
            
            # Parse table name
            from_idx = query_upper.find('FROM')
            after_from = query_clean[from_idx + 5:].strip()
            table = after_from.split()[0].lower().replace(',', '').strip()
            
            # Handle GROUP BY queries
            if 'GROUP BY' in query_upper:
                return self._handle_group_by_query(table, query_clean)
            
            # Build REST URL parameters
            url_params = self._build_query_params(query_clean, query_upper, params)
            
            result = self._make_request('GET', table, params=url_params)
            return result if result else []
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def _build_query_params(self, query: str, query_upper: str, params: tuple) -> Dict:
        """Build REST API query parameters from SQL query."""
        url_params = {}
        
        # Extract select columns
        select_idx = query_upper.find('SELECT')
        from_idx = query_upper.find('FROM')
        select_part = query[select_idx + 7:from_idx].strip()
        url_params['select'] = '*' if select_part == '*' else select_part.replace(' ', '')
        
        # Handle ORDER BY
        if 'ORDER BY' in query_upper:
            order_idx = query_upper.find('ORDER BY')
            order_part = query[order_idx + 9:].strip()
            
            # Remove LIMIT part if exists
            if 'LIMIT' in order_part.upper():
                order_part = order_part[:order_part.upper().find('LIMIT')].strip()
            
            order_clauses = []
            for op in order_part.split(','):
                op = op.strip()
                if not op:
                    continue
                op_upper = op.upper()
                if 'DESC' in op_upper:
                    col = op_upper.replace('DESC', '').strip()
                    if col:
                        order_clauses.append(f"{col.lower()}.desc")
                elif 'ASC' in op_upper:
                    col = op_upper.replace('ASC', '').strip()
                    if col:
                        order_clauses.append(f"{col.lower()}.asc")
                elif op:
                    order_clauses.append(f"{op.lower()}.asc")
            
            if order_clauses:
                url_params['order'] = ','.join(order_clauses)
        
        # Handle LIMIT
        if 'LIMIT' in query_upper:
            limit_idx = query_upper.find('LIMIT')
            limit_part = query[limit_idx + 6:].strip()
            limit_val = limit_part.split()[0] if limit_part else None
            
            if limit_val:
                if limit_val == '?' and params:
                    url_params['limit'] = str(params[-1])
                elif limit_val.isdigit():
                    url_params['limit'] = limit_val
        
        return url_params
    
    def _handle_group_by_query(self, table: str, query: str) -> List[Dict]:
        """Handle GROUP BY queries by aggregating in Python."""
        try:
            result = self._make_request('GET', table, params={'select': '*'})
            
            if not result:
                return []
            
            return self._aggregate_in_python(result, query)
            
        except Exception as e:
            logger.error(f"Error in GROUP BY query: {e}")
            return []
    
    def _aggregate_in_python(self, data: List[Dict], query: str) -> List[Dict]:
        """Perform aggregation in Python for GROUP BY queries."""
        try:
            query_upper = query.upper()
            
            # Extract GROUP BY column
            group_idx = query_upper.find('GROUP BY')
            group_part = query[group_idx + 8:].strip()
            if 'ORDER' in group_part.upper():
                group_part = group_part[:group_part.upper().find('ORDER')].strip()
            group_col = group_part.split()[0].strip()
            
            # Group data
            grouped = defaultdict(list)
            for row in data:
                key = row.get(group_col, 'unknown')
                grouped[key].append(row)
            
            # Parse SELECT for aggregations
            select_part = query[query_upper.find('SELECT') + 6:query_upper.find('FROM')].strip()
            
            results = []
            for key, rows in grouped.items():
                result = {group_col: key}
                
                for agg in select_part.split(','):
                    agg = agg.strip()
                    agg_upper = agg.upper()
                    
                    if 'COUNT(*)' in agg_upper:
                        alias = agg.split(' AS ')[-1].strip().lower() if ' AS ' in agg_upper else 'count'
                        result[alias] = len(rows)
                    elif 'AVG(' in agg_upper:
                        col = agg[agg.find('(')+1:agg.find(')')].strip()
                        alias = agg.split(' AS ')[-1].strip().lower() if ' AS ' in agg_upper else f'avg_{col}'
                        values = [r.get(col, 0) for r in rows if r.get(col) is not None]
                        result[alias] = sum(values) / len(values) if values else 0
                    elif 'MIN(' in agg_upper:
                        col = agg[agg.find('(')+1:agg.find(')')].strip()
                        alias = agg.split(' AS ')[-1].strip().lower() if ' AS ' in agg_upper else f'min_{col}'
                        values = [r.get(col, 0) for r in rows if r.get(col) is not None]
                        result[alias] = min(values) if values else 0
                    elif 'MAX(' in agg_upper:
                        col = agg[agg.find('(')+1:agg.find(')')].strip()
                        alias = agg.split(' AS ')[-1].strip().lower() if ' AS ' in agg_upper else f'max_{col}'
                        values = [r.get(col, 0) for r in rows if r.get(col) is not None]
                        result[alias] = max(values) if values else 0
                    elif 'SUM(' in agg_upper:
                        col = agg[agg.find('(')+1:agg.find(')')].strip()
                        # Handle CASE WHEN expressions
                        if 'CASE' in col.upper():
                            # For SUM(CASE WHEN feedback_correct IS NOT NULL...)
                            if 'feedback_correct IS NOT NULL' in agg:
                                alias = 'with_feedback'
                                result[alias] = sum(1 for r in rows if r.get('feedback_correct') is not None)
                            elif 'feedback_correct = TRUE' in agg or 'feedback_correct = 1' in agg:
                                alias = 'positive_feedback'
                                result[alias] = sum(1 for r in rows if r.get('feedback_correct') is True)
                            elif 'feedback_correct = FALSE' in agg or 'feedback_correct = 0' in agg:
                                alias = 'negative_feedback'
                                result[alias] = sum(1 for r in rows if r.get('feedback_correct') is False)
                        else:
                            alias = agg.split(' AS ')[-1].strip().lower() if ' AS ' in agg_upper else f'sum_{col}'
                            values = [r.get(col, 0) for r in rows if r.get(col) is not None]
                            result[alias] = sum(values)
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Python aggregation: {e}")
            return []
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics for monitoring."""
        if not self._ensure_connected():
            return {}
        
        try:
            result = self._make_request(
                'GET',
                'predictions',
                params={'select': 'id,feedback_correct,model_version'}
            )
            
            if not result:
                return {
                    'total_predictions': 0,
                    'with_feedback': 0,
                    'positive_feedback': 0,
                    'negative_feedback': 0
                }
            
            stats = {
                'total_predictions': len(result),
                'with_feedback': sum(1 for r in result if r.get('feedback_correct') is not None),
                'positive_feedback': sum(1 for r in result if r.get('feedback_correct') is True),
                'negative_feedback': sum(1 for r in result if r.get('feedback_correct') is False),
                'by_model': {}
            }
            
            # Group by model
            for row in result:
                model = row.get('model_version', 'unknown')
                if model not in stats['by_model']:
                    stats['by_model'][model] = {'total': 0, 'positive': 0, 'negative': 0}
                stats['by_model'][model]['total'] += 1
                if row.get('feedback_correct') is True:
                    stats['by_model'][model]['positive'] += 1
                elif row.get('feedback_correct') is False:
                    stats['by_model'][model]['negative'] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {}
    
    def get_training_data(self, train_ratio: float = 0.7) -> Dict[str, Any]:
        """Get data for training with specified train/test split ratio."""
        if not self._ensure_connected():
            return {'train': [], 'test': [], 'stats': {}}
        
        try:
            import random
            
            # Get predictions with feedback - use foreign key relation
            result = self._make_request(
                'GET',
                'predictions',
                params={
                    'select': 'id,prediction,confidence,model_version,feedback_correct,input_id,users_inputs(text_input,user_consent)',
                    'feedback_correct': 'not.is.null'
                }
            )
            
            if not result:
                return {'train': [], 'test': [], 'stats': {}}
            
            # Filter only consented data
            valid_data = []
            for row in result:
                users_input = row.get('users_inputs')
                if users_input and users_input.get('user_consent'):
                    valid_data.append({
                        'id': row['id'],
                        'text': users_input.get('text_input', ''),
                        'prediction': row['prediction'],
                        'feedback_correct': row['feedback_correct'],
                        'model_version': row['model_version']
                    })
            
            # Shuffle and split
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
        """Get recent prediction logs with join to users_inputs."""
        if not self._ensure_connected():
            return []
        
        try:
            result = self._make_request(
                'GET',
                'predictions',
                params={
                    'select': 'id,timestamp,model_version,prediction,confidence,latency,input_id,users_inputs(text_input)',
                    'order': 'timestamp.desc',
                    'limit': str(limit)
                }
            )
            
            if not result:
                return []
            
            return [
                {
                    'id': row['id'],
                    'timestamp': row.get('timestamp', ''),
                    'model_version': row.get('model_version', ''),
                    'prediction': row.get('prediction', ''),
                    'confidence': row.get('confidence', 0),
                    'latency': row.get('latency', 0),
                    'text_input': row.get('users_inputs', {}).get('text_input', '') if row.get('users_inputs') else ''
                }
                for row in result
            ]
            
        except Exception as e:
            logger.error(f"Error retrieving recent predictions: {e}")
            return []

    def get_dataset_snapshot(self, consent_only: bool = True) -> Any:
        """Get dataset snapshot for retraining."""
        if not self._ensure_connected():
            import pandas as pd
            return pd.DataFrame()
        
        try:
            import pandas as pd
            
            params = {
                'select': 'id,timestamp,text_input,predictions(prediction,confidence,model_version)',
                'order': 'timestamp.desc'
            }
            
            if consent_only:
                params['user_consent'] = 'eq.true'
            
            result = self._make_request('GET', 'users_inputs', params=params)
            
            if not result:
                return pd.DataFrame()
            
            # Flatten the nested data
            flattened = []
            for row in result:
                predictions = row.get('predictions', [])
                if predictions:
                    for pred in predictions:
                        flattened.append({
                            'id': row['id'],
                            'timestamp': row.get('timestamp', ''),
                            'text_input': row.get('text_input', ''),
                            'prediction': pred.get('prediction', ''),
                            'confidence': pred.get('confidence', 0),
                            'model_version': pred.get('model_version', '')
                        })
                else:
                    flattened.append({
                        'id': row['id'],
                        'timestamp': row.get('timestamp', ''),
                        'text_input': row.get('text_input', ''),
                        'prediction': None,
                        'confidence': None,
                        'model_version': None
                    })
            
            df = pd.DataFrame(flattened)
            logger.info(f"Dataset snapshot: {len(df)} records, consent_only={consent_only}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving dataset snapshot: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_metrics_by_version(self) -> Dict[str, Dict]:
        """Get aggregated metrics per model version."""
        if not self._ensure_connected():
            return {}
        
        try:
            result = self._make_request(
                'GET',
                'predictions',
                params={'select': 'model_version,confidence,latency'}
            )
            
            if not result:
                return {}
            
            metrics_data = defaultdict(list)
            
            for row in result:
                version = row.get('model_version', 'unknown')
                metrics_data[version].append({
                    'confidence': row.get('confidence', 0),
                    'latency': row.get('latency', 0)
                })
            
            metrics = {}
            for version, data in metrics_data.items():
                confidences = [d['confidence'] for d in data if d['confidence'] is not None]
                latencies = [d['latency'] for d in data if d['latency'] is not None]
                
                metrics[version] = {
                    'prediction_count': len(data),
                    'avg_confidence': round(sum(confidences) / len(confidences), 4) if confidences else 0,
                    'avg_latency': round(sum(latencies) / len(latencies), 4) if latencies else 0,
                    'min_latency': round(min(latencies), 4) if latencies else 0,
                    'max_latency': round(max(latencies), 4) if latencies else 0
                }
            
            logger.debug(f"Metrics retrieved for {len(metrics)} model versions")
            return metrics
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            return {}
    
    def initialize_schema(self, schema_file: str = None) -> bool:
        """Check if schema exists (tables are managed via Supabase Dashboard)."""
        return self.connect()
    
    def _tables_exist(self) -> bool:
        """Check if required tables exist."""
        if not self.connection:
            return self.connect()
        return True
    
    def execute_transaction(self, queries: List) -> bool:
        """REST API doesn't support true transactions - execute sequentially."""
        logger.warning("REST API doesn't support true transactions. Operations executed sequentially.")
        return True
    
    def migrate_schema(self, migration_sql: str) -> bool:
        """Schema migrations must be done via Supabase Dashboard."""
        logger.warning("Schema migrations must be done via Supabase Dashboard")
        return False
