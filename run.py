"""
Run script for Ghostx
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the absolute path of the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent

# Add the project root directory to Python path
sys.path.insert(0, str(PROJECT_ROOT))

from src import create_app
from src.config import DOMAIN
from waitress import serve

def get_server_mode():
    while True:
        print("\nChoose server mode:")
        print("1. Development (Local)")
        print("2. Production")
        choice = input("Enter your choice (1/2): ").strip()
        
        if choice == "1":
            return "development"
        elif choice == "2":
            return "production"
        else:
            print("Invalid choice. Please enter 1 or 2.")

def configure_environment(mode):
    """Configure environment variables based on selected mode"""
    os.environ['FLASK_ENV'] = mode
    
    if mode == 'development':
        os.environ['PORT'] = os.getenv('DEV_PORT', '5000')
        os.environ['HOST'] = os.getenv('DEV_HOST', '127.0.0.1')
        os.environ['DOMAIN'] = os.getenv('DEV_DOMAIN', 'localhost:5000')
        os.environ['DOMAIN_SCHEME'] = os.getenv('DEV_DOMAIN_SCHEME', 'http')
        os.environ['FLASK_DEBUG'] = 'True'
    else:
        os.environ['PORT'] = os.getenv('PROD_PORT', '80')
        os.environ['HOST'] = os.getenv('PROD_HOST', '0.0.0.0')
        os.environ['DOMAIN'] = os.getenv('PROD_DOMAIN')  # Use your Namecheap domain
        os.environ['DOMAIN_SCHEME'] = os.getenv('PROD_DOMAIN_SCHEME', 'http')
        os.environ['FLASK_DEBUG'] = 'False'

app = create_app()

if __name__ == "__main__":
    # Get server mode from user input
    mode = get_server_mode()
    
    # Configure environment variables
    configure_environment(mode)
    
    # Get configured settings
    host = os.getenv('HOST')
    port = int(os.getenv('PORT'))
    domain = os.getenv('DOMAIN')
    
    if mode == 'development':
        # Use Flask's development server
        print(f"\nStarting development server on http://{host}:{port}")
        print("Debug mode is ON")
        print("Press CTRL+C to stop the server")
        app.run(
            host=host,
            port=port,
            debug=True
        )
    else:
        # Use waitress for production
        print(f"\nStarting production server on http://{domain}")
        print("Running with Waitress WSGI server")
        print("Press CTRL+C to stop the server")
        
        # Always bind to all interfaces in production
        serve(
            app,
            host='0.0.0.0',  # Force binding to all interfaces
            port=port,
            url_scheme=os.getenv('DOMAIN_SCHEME'),
            threads=4,  # Optimize thread count
            connection_limit=1000,  # Set connection limit
            cleanup_interval=30  # Regular cleanup
        ) 