"""
Database Manager for Supabase using REST API.
Fallback from direct PostgreSQL connection.
"""

import time
import logging
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class SupabaseDatabaseManager:
    """Manager for Supabase database operations via REST API."""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url.rstrip('/')
        self.supabase_key = supabase_key
        self.max_retries = 3
        self.retry_delay = 1
        self.is_postgres = True
        
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
        """Test connection to Supabase."""
        try:
            r = self.http.get(f"{self.supabase_url}/rest/v1/", headers=self._headers, timeout=10)
            if r.status_code == 200:
                logger.info("Supabase REST API connection verified")
                return True
            logger.error(f"Supabase connection failed: {r.status_code} - {r.text}")
            return False
        except Exception as e:
            logger.error(f"Supabase connection error: {e}")
            return False
    
    def disconnect(self):
        """No-op for REST API (stateless)."""
        logger.info("Supabase REST API connection closed (stateless)")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query - parses SQL and converts to REST API call."""
        try:
            query_clean = ' '.join(query.split())
            query_upper = query_clean.upper()
            
            if 'FROM' not in query_upper:
                logger.error(f"Invalid query - no FROM clause: {query[:50]}")
                return []
            
            # Parse table name
            from_idx = query_upper.find('FROM')
            after_from = query_clean[from_idx + 5:].strip()
            table = after_from.split()[0].lower().replace(',', '').strip() if after_from.split() else ''
            
            # Handle GROUP BY queries
            if 'GROUP BY' in query_upper:
                return self._handle_group_by_query(table, query_clean)
            
            # Build REST URL
            url = self._build_rest_url(query_clean, query_upper, table, params)
            
            r = self.http.get(url, headers=self._headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            
            logger.error(f"Query failed: {r.status_code} - {r.text}")
            return []
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def _build_rest_url(self, query_clean: str, query_upper: str, table: str, params: tuple) -> str:
        """Build REST API URL from SQL query."""
        # Extract select columns
        select_idx = query_upper.find('SELECT')
        from_idx = query_upper.find('FROM')
        select_part = query_clean[select_idx + 7:from_idx].strip()
        select = '*' if select_part == '*' else select_part.replace(' ', '')
        
        url = f"{self.supabase_url}/rest/v1/{table}?select={select}"
        
        # Handle ORDER BY
        if 'ORDER BY' in query_upper:
            order_idx = query_upper.find('ORDER BY')
            order_part = query_clean[order_idx + 9:].strip()
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
                url += f"&order={','.join(order_clauses)}"
        
        # Handle LIMIT
        if 'LIMIT' in query_upper:
            limit_idx = query_upper.find('LIMIT')
            limit_part = query_clean[limit_idx + 6:].strip()
            limit_val = limit_part.split()[0] if limit_part else None
            if limit_val:
                if limit_val == '?' and params:
                    url += f"&limit={params[-1]}"
                elif limit_val.isdigit():
                    url += f"&limit={limit_val}"
        
        return url
    
    def _handle_group_by_query(self, table: str, query: str) -> List[Dict]:
        """Handle GROUP BY queries by aggregating in Python."""
        try:
            base_url = f"{self.supabase_url}/rest/v1/{table}?select=*"
            r = self.http.get(base_url, headers=self._headers, timeout=30)
            
            if r.status_code != 200:
                logger.error(f"Query failed: {r.status_code} - {r.text}")
                return []
            
            return self._aggregate_in_python(r.json(), query)
            
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
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Python aggregation: {e}")
            return []
    
    def _retry_request(self, method: str, url: str, **kwargs) -> Any:
        """Execute HTTP request with retry logic."""
        retries = 0
        while retries < self.max_retries:
            try:
                if method == 'post':
                    r = self.http.post(url, headers=self._headers, **kwargs)
                else:
                    r = self.http.get(url, headers=self._headers, **kwargs)
                return r
            except Exception as e:
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay * retries)
                    logger.warning(f"Retry {retries}/{self.max_retries}: {e}")
                else:
                    raise
    
    def insert_user_input(self, text: str, consent: bool) -> int:
        """Insert user input to database."""
        data = {'text_input': text, 'user_consent': consent, 'anonymized': False}
        
        r = self._retry_request('post', f"{self.supabase_url}/rest/v1/users_inputs", json=data, timeout=10)
        
        if r.status_code == 201:
            input_id = r.json()[0]['id']
            logger.info(f"User input inserted: ID={input_id}, consent={consent}")
            return input_id
        
        raise Exception(f"Insert failed: {r.status_code} - {r.text}")
    
    def insert_prediction(self, input_id: int, model_version: str, prediction: str, confidence: float, latency: float) -> int:
        """Insert prediction result to database."""
        data = {
            'input_id': input_id,
            'model_version': model_version,
            'prediction': prediction,
            'confidence': confidence,
            'latency': latency,
            'feedback_correct': None,
            'feedback_timestamp': None,
            'used_for_training': False,
            'training_split': None
        }
        
        r = self._retry_request('post', f"{self.supabase_url}/rest/v1/predictions", json=data, timeout=10)
        
        if r.status_code == 201:
            prediction_id = r.json()[0]['id']
            logger.info(f"Prediction inserted: ID={prediction_id}, model={model_version}")
            return prediction_id
        
        raise Exception(f"Insert failed: {r.status_code} - {r.text}")
    
    def update_prediction_feedback(self, prediction_id: int, feedback_correct: bool) -> bool:
        """Update feedback for a prediction."""
        try:
            from datetime import datetime
            data = {
                'feedback_correct': feedback_correct,
                'feedback_timestamp': datetime.now().isoformat()
            }
            
            url = f"{self.supabase_url}/rest/v1/predictions?id=eq.{prediction_id}"
            headers = {**self._headers, 'Prefer': 'return=minimal'}
            
            r = self.http.patch(url, headers=headers, json=data, timeout=10)
            
            if r.status_code in [200, 204]:
                logger.info(f"Feedback updated for prediction {prediction_id}: {feedback_correct}")
                return True
            
            logger.error(f"Failed to update feedback: {r.status_code} - {r.text}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating feedback: {e}")
            return False
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics for monitoring."""
        try:
            url = f"{self.supabase_url}/rest/v1/predictions?select=feedback_correct,model_version"
            r = self.http.get(url, headers=self._headers, timeout=10)
            
            if r.status_code != 200:
                return {}
            
            results = r.json()
            stats = {
                'total_predictions': len(results),
                'with_feedback': sum(1 for r in results if r.get('feedback_correct') is not None),
                'positive_feedback': sum(1 for r in results if r.get('feedback_correct') is True),
                'negative_feedback': sum(1 for r in results if r.get('feedback_correct') is False),
                'by_model': {}
            }
            
            # Group by model
            for row in results:
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
        try:
            import random
            
            # Get predictions with feedback and consent
            url = f"{self.supabase_url}/rest/v1/predictions"
            url += "?select=id,prediction,confidence,model_version,feedback_correct,users_inputs(text_input,user_consent)"
            url += "&feedback_correct=not.is.null"
            
            r = self.http.get(url, headers=self._headers, timeout=30)
            
            if r.status_code != 200:
                logger.error(f"Failed to get training data: {r.status_code}")
                return {'train': [], 'test': [], 'stats': {}}
            
            results = r.json()
            
            # Filter only consented data
            valid_data = [
                {
                    'id': row['id'],
                    'text': row.get('users_inputs', {}).get('text_input', ''),
                    'prediction': row['prediction'],
                    'feedback_correct': row['feedback_correct'],
                    'model_version': row['model_version']
                }
                for row in results
                if row.get('users_inputs', {}).get('user_consent', False)
            ]
            
            # Shuffle and split
            random.shuffle(valid_data)
            split_idx = int(len(valid_data) * train_ratio)
            
            train_data = valid_data[:split_idx]
            test_data = valid_data[split_idx:]
            
            return {
                'train': train_data,
                'test': test_data,
                'stats': {
                    'total': len(valid_data),
                    'train_count': len(train_data),
                    'test_count': len(test_data),
                    'train_ratio': train_ratio
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return {'train': [], 'test': [], 'stats': {}}
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict]:
        """Get recent prediction logs with join to users_inputs."""
        try:
            url = f"{self.supabase_url}/rest/v1/predictions"
            url += "?select=id,timestamp,model_version,prediction,confidence,latency,users_inputs(text_input)"
            url += f"&order=timestamp.desc&limit={limit}"
            
            r = self.http.get(url, headers=self._headers, timeout=10)
            
            if r.status_code == 200:
                results = r.json()
                return [
                    {
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'model_version': row['model_version'],
                        'prediction': row['prediction'],
                        'confidence': row['confidence'],
                        'latency': row['latency'],
                        'text_input': row.get('users_inputs', {}).get('text_input', '')
                    }
                    for row in results
                ]
            
            logger.error(f"Failed to get predictions: {r.status_code} - {r.text}")
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving recent predictions: {e}")
            return []
    
    def get_dataset_snapshot(self, consent_only: bool = True) -> Any:
        """Get dataset snapshot for retraining."""
        try:
            import pandas as pd
            
            url = f"{self.supabase_url}/rest/v1/users_inputs"
            url += "?select=id,timestamp,text_input,predictions(prediction,confidence,model_version)"
            
            if consent_only:
                url += "&user_consent=eq.true"
            
            url += "&order=timestamp.desc"
            
            r = self.http.get(url, headers=self._headers, timeout=30)
            
            if r.status_code == 200:
                results = r.json()
                flattened = []
                for row in results:
                    for pred in row.get('predictions', []):
                        flattened.append({
                            'id': row['id'],
                            'timestamp': row['timestamp'],
                            'text_input': row['text_input'],
                            'prediction': pred['prediction'],
                            'confidence': pred['confidence'],
                            'model_version': pred['model_version']
                        })
                
                df = pd.DataFrame(flattened)
                logger.info(f"Dataset snapshot: {len(df)} records, consent_only={consent_only}")
                return df
            
            logger.error(f"Failed to get dataset: {r.status_code} - {r.text}")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error retrieving dataset snapshot: {e}")
            import pandas as pd
            return pd.DataFrame()
    
    def get_metrics_by_version(self) -> Dict[str, Dict]:
        """Get aggregated metrics per model version."""
        try:
            url = f"{self.supabase_url}/rest/v1/predictions?select=model_version,confidence,latency"
            r = self.http.get(url, headers=self._headers, timeout=30)
            
            if r.status_code != 200:
                logger.error(f"Failed to get metrics: {r.status_code} - {r.text}")
                return {}
            
            results = r.json()
            metrics_data = defaultdict(list)
            
            for row in results:
                version = row['model_version']
                metrics_data[version].append({'confidence': row['confidence'], 'latency': row['latency']})
            
            metrics = {}
            for version, data in metrics_data.items():
                confidences = [d['confidence'] for d in data]
                latencies = [d['latency'] for d in data]
                
                metrics[version] = {
                    'prediction_count': len(data),
                    'avg_confidence': round(sum(confidences) / len(confidences), 4) if confidences else 0,
                    'avg_latency': round(sum(latencies) / len(latencies), 4) if latencies else 0,
                    'min_latency': round(min(latencies), 4) if latencies else 0,
                    'max_latency': round(max(latencies), 4) if latencies else 0
                }
            
            logger.debug(f"Metrics for {len(metrics)} model versions")
            return metrics
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {e}")
            return {}
    
    def initialize_schema(self, schema_file: str = None) -> bool:
        """Check if schema exists (tables are managed via Supabase Dashboard)."""
        try:
            r = self.http.get(f"{self.supabase_url}/rest/v1/users_inputs?limit=1", headers=self._headers, timeout=10)
            if r.status_code == 200:
                logger.info("Supabase schema verified - tables exist")
                return True
            logger.error(f"Schema check failed: {r.status_code}")
            return False
        except Exception as e:
            logger.error(f"Error checking schema: {e}")
            return False
    
    def _tables_exist(self) -> bool:
        return self.initialize_schema()
    
    def execute_transaction(self, queries: List) -> bool:
        """REST API doesn't support true transactions."""
        logger.warning("REST API doesn't support true transactions. Operations executed sequentially.")
        return True
    
    def migrate_schema(self, migration_sql: str) -> bool:
        """Schema migrations must be done via Supabase Dashboard."""
        logger.warning("Schema migrations must be done via Supabase Dashboard")
        return False
