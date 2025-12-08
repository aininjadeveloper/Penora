import sys
import os
sys.path.append(os.getcwd())

print("Attempting to import app...")
try:
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    from app import app
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
