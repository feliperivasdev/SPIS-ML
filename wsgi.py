import sys
import os

# Agregar el directorio dashboard al path
dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard')
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

print(f"[DEBUG] Python path: {sys.path[:3]}")
print(f"[DEBUG] Dashboard dir: {dashboard_dir}")
print(f"[DEBUG] App.py exists: {os.path.exists(os.path.join(dashboard_dir, 'app.py'))}")

try:
    print("[DEBUG] Importing app...")
    from app import server
    print("[DEBUG] Successfully imported app.server")
except Exception as e:
    print(f"[ERROR] Failed to import app: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    raise

if __name__ == "__main__":
    server.run(host='0.0.0.0', debug=False)
