from flask import Blueprint, render_template, redirect, url_for, current_app, jsonify, request
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from datetime import datetime, timedelta
from src.config import MAX_EMAILS_PER_HOUR, MAX_EMAILS_PER_DAY
from src.models import EmailTemplate, User
from src.routes.auth import user_required
from .. import db, logger
from ..utils.log_sanitizer import sanitize_user_data, sanitize_log

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