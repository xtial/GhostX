from flask import Blueprint, render_template, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from datetime import datetime, timedelta
from src.config import MAX_EMAILS_PER_HOUR, MAX_EMAILS_PER_DAY
from src.models import EmailTemplate
from src.routes.auth import user_required
import logging

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

@main.route('/')
def index():
    logger.debug("Accessing index route")
    if current_user.is_authenticated:
        logger.debug(f"User {current_user.username} is authenticated, redirecting to appropriate dashboard")
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))
    logger.debug("User not authenticated, showing index page")
    return render_template('index.html', csrf_token=generate_csrf())

@main.route('/dashboard')
@user_required
def dashboard():
    logger.debug(f"Rendering dashboard for user {current_user.username}")
    return render_template('dashboard.html', csrf_token=generate_csrf())

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
        logger.error(f"Error getting user limits: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get email limits'
        }), 500 

@main.route('/api/templates')
@login_required
def get_templates():
    try:
        templates = EmailTemplate.query.all()
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
        logger.error(f"Error getting email templates: {str(e)}")
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
        logger.error(f"Error getting email template: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load template'
        }), 500 