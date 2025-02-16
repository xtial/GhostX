import os
import sys
import click
from src import create_app, db
from src.models import (
    User, UserRole, Session, LoginAttempt, 
    APIRequest, SecurityLog, EmailTemplate, Permission
)
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import inspect

def table_exists(engine, table_name):
    """Check if a table exists"""
    return inspect(engine).has_table(table_name)

def cleanup_database():
    """Clean up all tables in the database"""
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Drop tables in correct order
        if 'security_logs' in tables:
            SecurityLog.__table__.drop(db.engine)
        if 'api_requests' in tables:
            APIRequest.__table__.drop(db.engine)
        if 'login_attempts' in tables:
            LoginAttempt.__table__.drop(db.engine)
        if 'sessions' in tables:
            Session.__table__.drop(db.engine)
        if 'email_templates' in tables:
            EmailTemplate.__table__.drop(db.engine)
        if 'user_permissions' in tables:
            db.Table('user_permissions',
                db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id')),
                extend_existing=True
            ).drop(db.engine)
        if 'permissions' in tables:
            Permission.__table__.drop(db.engine)
        if 'users' in tables:
            User.__table__.drop(db.engine)
        
        # Clear any remaining sessions
        db.session.remove()
        
    except Exception as e:
        click.echo(f'Warning during cleanup: {str(e)}')

def create_security_tables(db_session):
    """Create security tables using both SQLAlchemy and direct SQL"""
    tables = {
        'sessions': Session.__table__,
        'login_attempts': LoginAttempt.__table__,
        'api_requests': APIRequest.__table__,
        'security_logs': SecurityLog.__table__
    }
    
    for table_name, table in tables.items():
        if not table_exists(db.engine, table_name):
            try:
                table.create(db.engine)
                click.echo(f'Created table {table_name}')
            except Exception as e:
                click.echo(f'SQLAlchemy creation failed for {table_name}, falling back to SQL')
                # If SQLAlchemy fails, fall back to direct SQL
                if table_name == 'sessions':
                    db_session.execute('''
                        CREATE TABLE IF NOT EXISTS sessions (
                            id VARCHAR(36) PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            ip_address VARCHAR(45) NOT NULL,
                            user_agent VARCHAR(255),
                            created_at DATETIME NOT NULL,
                            last_active DATETIME NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                elif table_name == 'login_attempts':
                    db_session.execute('''
                        CREATE TABLE IF NOT EXISTS login_attempts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username VARCHAR(255) NOT NULL,
                            ip_address VARCHAR(45) NOT NULL,
                            success BOOLEAN DEFAULT FALSE,
                            timestamp DATETIME NOT NULL,
                            user_agent VARCHAR(255)
                        )
                    ''')
                elif table_name == 'api_requests':
                    db_session.execute('''
                        CREATE TABLE IF NOT EXISTS api_requests (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            endpoint VARCHAR(255) NOT NULL,
                            method VARCHAR(10) NOT NULL,
                            user_id INTEGER,
                            ip_address VARCHAR(45) NOT NULL,
                            status_code INTEGER,
                            timestamp DATETIME NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')
                elif table_name == 'security_logs':
                    db_session.execute('''
                        CREATE TABLE IF NOT EXISTS security_logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title VARCHAR(255) NOT NULL,
                            message TEXT NOT NULL,
                            severity VARCHAR(20) NOT NULL,
                            user_id INTEGER,
                            timestamp DATETIME NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users (id)
                        )
                    ''')

@click.command()
@click.option('--remake', is_flag=True, help='Recreate the database from scratch')
def setup_db(remake):
    """Initialize the database."""
    app = create_app()
    app.app_context().push()
    
    try:
        if remake:
            click.echo('Removing existing database...')
            if os.path.exists('spoofer.db'):
                os.remove('spoofer.db')
            
            click.echo('Cleaning up existing tables...')
            cleanup_database()
            
            click.echo('Creating new database...')
            db.create_all()
            
            # Create initial admin user with minimal required fields
            admin = User(
                username='admin',
                email='admin@domain.com',
                role=UserRole.ADMIN.value,
                is_admin=True,
                is_active=True,
                join_date=datetime.now(timezone.utc),
                email_count=0,
                daily_email_count=0,
                last_hourly_reset=datetime.now(timezone.utc),
                last_daily_reset=datetime.now(timezone.utc),
                successful_emails=0,
                failed_emails=0,
                total_campaigns=0,
                total_templates=0,
                total_opens=0,
                total_clicks=0,
                failed_login_attempts=0,
                email_notifications=True,
                two_factor_enabled=False,
                registration_ip='127.0.0.1',
                last_login_ip='127.0.0.1',
                last_login_date=datetime.now(timezone.utc)
            )
            admin.set_password('admin')
            
            # Check if admin user already exists
            existing_admin = User.query.filter_by(username='admin').first()
            if existing_admin:
                click.echo('Admin user already exists, updating password and admin status...')
                existing_admin.password_hash = admin.password_hash
                existing_admin.is_admin = True
                existing_admin.role = UserRole.ADMIN.value
                existing_admin.is_active = True
                db.session.commit()
            else:
                db.session.add(admin)
                db.session.commit()
            
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
                )
            ]
            
            for template in templates:
                db.session.add(template)
            
            db.session.commit()
            
            # Add initial security log
            security_log = SecurityLog(
                title="System Initialization",
                message="Database initialized with admin user and default templates",
                severity="info",
                user_id=1,
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(security_log)
            
            db.session.commit()
            click.echo('Created/updated admin user (username: admin, password: admin)')
            click.echo('Added default email templates')
            
        # Create security tables using both methods for reliability
        click.echo('Ensuring security tables exist...')
        create_security_tables(db.session)
        
        db.session.commit()
        click.echo('Security tables created/updated successfully')
        click.echo('Database setup completed successfully!')
        
    except Exception as e:
        click.echo(f'Error: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    setup_db() 