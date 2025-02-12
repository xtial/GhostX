#!/usr/bin/env python3
from setuptools import setup, find_packages
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

def get_server_mode():
    """Get server mode from user input"""
    while True:
        print("\nGhostx Server Configuration")
        print("==========================")
        print("1. Development Mode (Debug ON, Local)")
        print("2. Production Mode (Debug OFF, Public)")
        print("3. Shell Mode (Interactive Python)")
        print("4. Database Migration")
        print("5. Exit")
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice in ["1", "2", "3", "4", "5"]:
            return choice
        else:
            print("\nInvalid choice. Please enter a number between 1 and 5.")

def configure_environment(mode):
    """Configure environment variables based on selected mode"""
    if mode == "1":  # Development
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = 'True'
        os.environ['PORT'] = os.getenv('DEV_PORT', '5000')
        os.environ['HOST'] = os.getenv('DEV_HOST', '127.0.0.1')
        os.environ['DOMAIN'] = os.getenv('DEV_DOMAIN', 'localhost:5000')
        os.environ['DOMAIN_SCHEME'] = os.getenv('DEV_DOMAIN_SCHEME', 'http')
    elif mode == "2":  # Production
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = 'False'
        os.environ['PORT'] = os.getenv('PROD_PORT', '80')
        os.environ['HOST'] = os.getenv('PROD_HOST', '0.0.0.0')
        os.environ['DOMAIN'] = os.getenv('DOMAIN', 'ghost.sbs')
        os.environ['DOMAIN_SCHEME'] = os.getenv('DOMAIN_SCHEME', 'http')

def run_server():
    """Run the Flask application"""
    mode = get_server_mode()
    
    if mode == "5":  # Exit
        print("\nExiting Ghostx server...")
        sys.exit(0)
        
    if mode == "3":  # Shell Mode
        print("\nStarting Python shell with Ghostx context...")
        from src import create_app
        app = create_app()
        ctx = app.app_context()
        ctx.push()
        import code
        code.interact(local=locals())
        return
        
    if mode == "4":  # Database Migration
        while True:
            print("\nDatabase Migration Options")
            print("1. Create new migration")
            print("2. Upgrade database")
            print("3. Downgrade database")
            print("4. Back to main menu")
            db_choice = input("\nEnter your choice (1-4): ").strip()
            
            if db_choice == "1":
                message = input("Enter migration message: ")
                os.system(f'flask db migrate -m "{message}"')
            elif db_choice == "2":
                os.system('flask db upgrade')
            elif db_choice == "3":
                os.system('flask db downgrade')
            elif db_choice == "4":
                run_server()  # Back to main menu
            else:
                print("Invalid choice. Please try again.")
        return

    # Configure environment for development or production
    configure_environment(mode)
    
    # Import here to use configured environment
    from src import create_app
    from waitress import serve
    
    app = create_app()
    host = os.getenv('HOST')
    port = int(os.getenv('PORT'))
    
    if mode == "1":  # Development
        print(f"\nStarting development server at http://{host}:{port}")
        print("Debug mode: ON")
        print("Press CTRL+C to stop")
        app.run(host=host, port=port, debug=True)
    else:  # Production
        print(f"\nStarting production server at http://{os.getenv('DOMAIN')}")
        print("Debug mode: OFF")
        print("Press CTRL+C to stop")
        serve(
            app,
            host=host,
            port=port,
            url_scheme=os.getenv('DOMAIN_SCHEME'),
            threads=4,
            connection_limit=1000,
            cleanup_interval=30
        )

# Read README and requirements
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Setup configuration
setup(
    name="ghostx",
    version="1.0.0",
    author="Ghostx Team",
    author_email="admin@ghost.sbs",
    description="Professional Email Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GhostRelayX/spoofer.git",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "ghostx=setup:run_server",
        ],
    },
)

if __name__ == "__main__":
    run_server() 