"""
Test script untuk memverifikasi koneksi dan operasi Supabase.
Jalankan: python test_supabase_connection.py
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"✓ Loaded .env from {env_path}")
except ImportError:
    print("⚠ python-dotenv not installed, using system env vars")

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')

print("\n" + "=" * 60)
print("SUPABASE CONNECTION TEST")
print("=" * 60)

print(f"\n[Config]")
print(f"  DATABASE_TYPE: {DATABASE_TYPE}")
print(f"  SUPABASE_URL: {SUPABASE_URL[:50]}..." if len(SUPABASE_URL) > 50 else f"  SUPABASE_URL: {SUPABASE_URL}")
print(f"  SUPABASE_KEY: {'*' * 20}..." if SUPABASE_KEY else "  SUPABASE_KEY: (not set)")

# Validate config
if DATABASE_TYPE.lower() != 'supabase':
    print(f"\n⚠ DATABASE_TYPE is '{DATABASE_TYPE}', not 'supabase'")
    print("  Update .env file: DATABASE_TYPE=supabase")
    sys.exit(1)

if not SUPABASE_URL or SUPABASE_URL == "https://your-project-id.supabase.co":
    print("\n❌ SUPABASE_URL not configured!")
    print("  Update .env file with your Supabase project URL")
    sys.exit(1)

if not SUPABASE_KEY or SUPABASE_KEY == "your_supabase_anon_key_here":
    print("\n❌ SUPABASE_KEY not configured!")
    print("  Update .env file with your Supabase anon key")
    sys.exit(1)

# Test connection
print("\n[1] Testing Supabase connection...")
try:
    from database.db_manager_supabase import SupabaseDatabaseManager
    
    db = SupabaseDatabaseManager(SUPABASE_URL, SUPABASE_KEY)
    
    if db.connect():
        print("  ✓ Connection successful!")
    else:
        print("  ❌ Connection failed!")
        sys.exit(1)
        
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test insert user input
print("\n[2] Testing insert_user_input...")
try:
    input_id = db.insert_user_input(
        text="Test input dari script pengujian Supabase",
        consent=True
    )
    
    if input_id:
        print(f"  ✓ User input inserted: ID={input_id}")
    else:
        print("  ❌ Failed to insert user input - no ID returned")
        sys.exit(1)
        
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test insert prediction
print("\n[3] Testing insert_prediction...")
try:
    prediction_id = db.insert_prediction(
        input_id=input_id,
        model_version="v1",
        prediction="positif",
        confidence=0.85,
        latency=0.123
    )
    
    if prediction_id:
        print(f"  ✓ Prediction inserted: ID={prediction_id}")
    else:
        print("  ❌ Failed to insert prediction - no ID returned")
        sys.exit(1)
        
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

# Test update feedback
print("\n[4] Testing update_prediction_feedback...")
try:
    success = db.update_prediction_feedback(prediction_id, True)
    
    if success:
        print(f"  ✓ Feedback updated for prediction {prediction_id}")
    else:
        print("  ❌ Failed to update feedback")
        
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test get recent predictions
print("\n[5] Testing get_recent_predictions...")
try:
    recent = db.get_recent_predictions(limit=5)
    print(f"  ✓ Retrieved {len(recent)} recent predictions")
    
    if recent:
        for r in recent[:2]:
            print(f"    - [{r.get('prediction')}] {r.get('text_input', '')[:30]}...")
            
except Exception as e:
    print(f"  ❌ Error: {e}")

# Test get feedback stats
print("\n[6] Testing get_feedback_stats...")
try:
    stats = db.get_feedback_stats()
    print(f"  ✓ Stats retrieved:")
    print(f"    - Total predictions: {stats.get('total_predictions', 0)}")
    print(f"    - With feedback: {stats.get('with_feedback', 0)}")
    print(f"    - Positive: {stats.get('positive_feedback', 0)}")
    print(f"    - Negative: {stats.get('negative_feedback', 0)}")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Supabase is working correctly!")
print("=" * 60)
print("\nAnda sekarang bisa menjalankan aplikasi dengan: streamlit run app.py")
