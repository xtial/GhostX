from flask import Blueprint, render_template, redirect, url_for, current_app, jsonify, request, send_from_directory
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from datetime import datetime, timedelta
from src.config import MAX_EMAILS_PER_HOUR, MAX_EMAILS_PER_DAY
from src.models import EmailTemplate, User
from src.routes.auth import user_required
from .. import db, logger
from ..utils.log_sanitizer import sanitize_user_data, sanitize_log
import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    logger.info("Homepage accessed")
    if current_user.is_authenticated:
        logger.debug(f"User {current_user.username} is authenticated, redirecting to appropriate dashboard")
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))
    logger.debug("User not authenticated, showing index page")
    return render_template('index.html', csrf_token=generate_csrf())

@main.route('/dashboard')
@login_required
def dashboard():
    try:
        user_id = sanitize_user_data(str(current_user.id))
        logger.info(f"User {user_id} accessed dashboard")
        return render_template('dashboard.html', csrf_token=generate_csrf())
    except Exception as e:
        logger.error(f"Error accessing dashboard: {sanitize_log(str(e))}")
        return jsonify({'error': 'Internal server error'}), 500

@main.route('/api/limits')
@login_required
def get_limits():
    try:
        # Get the current hour's start time
        now = datetime.utcnow()
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count emails sent in the current hour and day
        hourly_sent = current_user.email_count - (current_user.last_hourly_reset or 0)
        daily_sent = current_user.email_count - (current_user.last_daily_reset or 0)
        
        # Calculate remaining limits
        hourly_remaining = max(0, MAX_EMAILS_PER_HOUR - hourly_sent)
        daily_remaining = max(0, MAX_EMAILS_PER_DAY - daily_sent)
        
        return jsonify({
            'success': True,
            'email_count': current_user.email_count,
            'hourly_remaining': hourly_remaining,
            'daily_remaining': daily_remaining
        })
        
    except Exception as e:
        logger.error(f"Error getting user limits: {sanitize_log(str(e))}")
        return jsonify({
            'success': False,
            'message': 'Failed to get email limits'
        }), 500 

@main.route('/api/templates')
@login_required
def get_templates():
    try:
        user_id = sanitize_user_data(str(current_user.id))
        templates = EmailTemplate.query.filter_by(user_id=current_user.id).all()
        logger.info(f"User {user_id} retrieved their email templates. Count: {len(templates)}")
        return jsonify({
            'success': True,
            'templates': [{
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'html_content': template.html_content
            } for template in templates]
        })
    except Exception as e:
        logger.error(f"Error retrieving templates: {sanitize_log(str(e))}")
        return jsonify({
            'success': False,
            'message': 'Failed to load templates'
        }), 500

@main.route('/api/templates/<int:template_id>')
@login_required
def get_template(template_id):
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': 'Template not found'
            }), 404
            
        return jsonify({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'html_content': template.html_content
            }
        })
    except Exception as e:
        logger.error(f"Error getting email template: {sanitize_log(str(e))}")
        return jsonify({
            'success': False,
            'message': 'Failed to load template'
        }), 500 

@main.route('/profile')
@login_required
def get_profile():
    try:
        user_id = sanitize_user_data(str(current_user.id))
        user = User.query.get_or_404(current_user.id)
        logger.info(f"User {user_id} accessed their profile")
        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving profile: {sanitize_log(str(e))}")
        return jsonify({'error': 'Internal server error'}), 500 

@main.route('/favicon.ico')
def favicon():
    """Serve the favicon"""
    try:
        return send_from_directory(
            os.path.join(os.path.dirname(current_app.root_path), 'static', 'favicon_io'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except Exception as e:
        logger.error(f"Error serving favicon: {sanitize_log(str(e))}")
        return '', 404 

@main.route('/api/templates/preview/<path:template_path>')
@login_required
def preview_template(template_path):
    """Preview a specific email template"""
    try:
        # First try to find template in database
        template = EmailTemplate.query.filter_by(name=template_path).first()
        
        if template:
            html_content = template.html_content
        else:
            # If not in database, try to load from static files
            # Construct the correct path to static/templates directory
            template_name = template_path.rstrip('.html')
            possible_paths = [
                os.path.join('static', 'templates', f"{template_name}.html"),
                os.path.join('static', 'templates', template_path)
            ]
            
            template_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    template_file = path
                    break
                    
            if not template_file:
                logger.error(f"Template not found: {template_path}")
                return jsonify({
                    'success': False,
                    'message': 'Template not found'
                }), 404
                
            with open(template_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        
        # Add preview wrapper with styles
        preview_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    margin: 0; 
                    padding: 20px; 
                    background: #f4f7fa;
                    font-family: Arial, sans-serif;
                }}
                .email-preview {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #fff;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    padding: 20px;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="email-preview">
                {html_content}
            </div>
        </body>
        </html>
        """
            
        return jsonify({
            'success': True,
            'html': preview_html,
            'filename': template_path
        })
    except Exception as e:
        logger.error(f"Error previewing template: {sanitize_log(str(e))}")
        return jsonify({
            'success': False,
            'message': f'Failed to load template preview: {str(e)}'
        }), 500 