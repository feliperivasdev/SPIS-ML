import sys
import os

# Agregar el directorio dashboard al path
dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard')
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

try:
    from app import server
except ImportError as e:
    print(f"Error importing app from {dashboard_dir}: {e}")
    raise

if __name__ == "__main__":
    server.run(host='0.0.0.0', debug=False)
