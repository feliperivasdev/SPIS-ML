import sys
import os

# Agregar el directorio dashboard al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard'))

from app import server

if __name__ == "__main__":
    server.run(host='0.0.0.0', debug=False)
