from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, text
from src.models import db, User, Session, LoginAttempt, APIRequest, SecurityLog, EmailTemplate, RegistrationAttempt
from src.utils.decorators import admin_required
from src.utils.security import check_system_status
from src.utils.log_sanitizer import sanitize_log
from src.utils.rate_limiter import limiter
from src.config import Config
import logging
import csv
import io
import os

logger = logging.getLogger(__name__)
admin_api = Blueprint('admin_api', __name__)

# All admin routes are exempt from rate limiting by default
limiter.exempt(admin_api)

@admin_api.route('/system-status')
@login_required
@admin_required
def get_system_status():
    """Get real-time system status"""
    try:
        status = check_system_status()
        return jsonify({
            'success': True,
            'api_status': status['api'],
            'db_status': status['database'],
            'email_status': status['email']
        })
    except Exception as e:
        logger.error(f"Error checking system status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to check system status'
        }), 500

@admin_api.route('/active-sessions')
@login_required
@admin_required
def get_active_sessions():
    """Get all active user sessions"""
    try:
        # Get sessions active in the last 30 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        active_sessions = Session.query.filter(Session.last_active >= cutoff).all()
        
        sessions = [{
            'id': session.id,
            'username': session.user.username,
            'ip': session.ip_address,
            'last_active': session.last_active.strftime('%Y-%m-%d %H:%M:%S'),
            'user_agent': session.user_agent
        } for session in active_sessions]
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get active sessions'
        }), 500

@admin_api.route('/security-metrics')
@login_required
@admin_required
def get_security_metrics():
    """Get real-time security metrics"""
    try:
        # Get metrics for the last hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        
        # Get login attempts grouped by 5-minute intervals using SQLite strftime
        login_attempts = db.session.query(
            func.strftime('%Y-%m-%d %H:%M', LoginAttempt.timestamp).label('interval'),
            func.count(LoginAttempt.id).label('count')
        ).filter(
            LoginAttempt.timestamp >= cutoff
        ).group_by(
            'interval'
        ).order_by(
            'interval'
        ).all()
        
        # Get API requests grouped by 5-minute intervals
        api_requests = db.session.query(
            func.strftime('%Y-%m-%d %H:%M', APIRequest.timestamp).label('interval'),
            func.count(APIRequest.id).label('count')
        ).filter(
            APIRequest.timestamp >= cutoff
        ).group_by(
            'interval'
        ).order_by(
            'interval'
        ).all()
        
        # Get recent security alerts
        alerts = SecurityLog.query.filter(
            SecurityLog.timestamp >= cutoff
        ).order_by(SecurityLog.timestamp.desc()).limit(10).all()
        
        # Format timestamps and ensure we have data for every 5-minute interval
        current_time = datetime.utcnow()
        intervals = []
        login_counts = []
        api_counts = []
        
        # Create a map of existing data
        login_data = {x[0]: x[1] for x in login_attempts}
        api_data = {x[0]: x[1] for x in api_requests}
        
        # Generate intervals for the last hour
        for i in range(12):  # 12 5-minute intervals in an hour
            interval_time = current_time - timedelta(minutes=i*5)
            interval_str = interval_time.strftime('%Y-%m-%d %H:%M')
            intervals.insert(0, interval_time.strftime('%H:%M'))
            login_counts.insert(0, login_data.get(interval_str, 0))
            api_counts.insert(0, api_data.get(interval_str, 0))
        
        return jsonify({
            'success': True,
            'timestamps': intervals,
            'login_attempts': login_counts,
            'api_requests': api_counts,
            'alerts': [{
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity,
                'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            } for alert in alerts]
        })
    except Exception as e:
        logger.error(f"Error getting security metrics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get security metrics'
        }), 500

@admin_api.route('/terminate-session', methods=['POST'])
@login_required
@admin_required
def terminate_session():
    """Terminate a specific user session"""
    try:
        session_id = request.json.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Session ID is required'
            }), 400
            
        session = Session.query.get(session_id)
        if not session:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
            
        db.session.delete(session)
        db.session.commit()
        
        # Log the action
        log = SecurityLog(
            title='Session Terminated',
            message=f'Admin {current_user.username} terminated session for user {session.user.username}',
            severity='medium',
            user_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Session terminated successfully'
        })
    except Exception as e:
        logger.error(f"Error terminating session: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to terminate session'
        }), 500

@admin_api.route('/terminate-all-sessions', methods=['POST'])
@login_required
@admin_required
def terminate_all_sessions():
    """Terminate all user sessions except the current admin session"""
    try:
        # Delete all sessions except current admin session
        Session.query.filter(Session.id != current_user.get_id()).delete()
        db.session.commit()
        
        # Log the action
        log = SecurityLog(
            title='All Sessions Terminated',
            message=f'Admin {current_user.username} terminated all user sessions',
            severity='high',
            user_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'All sessions terminated successfully'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error terminating all sessions: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to terminate sessions'
        }), 500

@admin_api.route('/security/logs/export')
@login_required
def export_security_logs():
    try:
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Timestamp', 'Event Type', 'User', 'IP Address', 'Details'])
        
        # Get logs from database
        logs = SecurityLog.query.order_by(SecurityLog.timestamp.desc()).all()
        
        # Write log entries
        for log in logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.event_type,
                log.user_id,
                log.ip_address,
                log.details
            ])
        
        # Prepare the CSV file
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'security_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to export security logs'
        }), 500

@admin_api.route('/templates/<path:template_path>')
@login_required
@admin_required
def get_template(template_path):
    """Get a specific email template"""
    try:
        # Handle template path to find the correct template
        template = EmailTemplate.query.filter_by(name=template_path).first()
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
        logger.error(f"Error getting template: {sanitize_log(str(e))}")
        return jsonify({
            'success': False,
            'message': 'Failed to load template'
        }), 500

@admin_api.route('/templates/<path:template_path>/preview')
@login_required
@admin_required
def preview_template(template_path):
    """Preview a specific email template"""
    try:
        # First try to find template in database
        template = EmailTemplate.query.filter_by(name=template_path).first()
        
        if template:
            html_content = template.html_content
        else:
            # If not in database, try to load from static files
            template_file = os.path.join(current_app.root_path, 'static', 'templates', template_path)
            if not os.path.exists(template_file):
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
                body {{ margin: 0; padding: 20px; }}
                .email-preview {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #fff;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            'message': 'Failed to load template preview'
        }), 500

@admin_api.route('/stats/charts')
@login_required
def get_chart_data():
    try:
        # Get activity data for the past 7 days
        activity_data = {
            'labels': [],
            'values': []
        }
        
        # TODO: Implement actual data gathering logic
        # This is just placeholder data
        activity_data['labels'] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        activity_data['values'] = [65, 59, 80, 81, 56, 55, 40]
        
        return jsonify({
            'success': True,
            'activity': activity_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Failed to load chart data'
        }), 500

@admin_api.route('/rate-limits/<int:user_id>')
@login_required
@admin_required
def get_user_rate_limits(user_id):
    """Get rate limits and usage for a specific user"""
    try:
        quota = limiter.get_remaining_quota(user_id)
        if not quota:
            return jsonify({
                'success': False,
                'message': 'Failed to get rate limit information'
            }), 404
            
        return jsonify({
            'success': True,
            'quota': quota
        })
    except Exception as e:
        logger.error(f"Error getting user rate limits: {sanitize_log(str(e))}")
        return jsonify({
            'success': False,
            'message': 'Failed to get rate limit information'
        }), 500

@admin_api.route('/rate-limits/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_rate_limits(user_id):
    """Update rate limits for a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
        data = request.get_json()
        hourly = data.get('hourly')
        daily = data.get('daily')
        concurrent = data.get('concurrent')
        
        if limiter.update_limits(user.role, hourly, daily, concurrent):
            return jsonify({
                'success': True,
                'message': 'Rate limits updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update rate limits'
            }), 400
            
    except Exception as e:
        logger.error(f"Error updating user rate limits: {sanitize_log(str(e))}")
        return jsonify({
            'success': False,
            'message': 'Failed to update rate limits'
        }), 500

@admin_api.route('/rate-limits/reset', methods=['POST'])
@login_required
@admin_required
def reset_rate_limits():
    """Reset all rate limits"""
    try:
        # Reset registration attempts
        success, message = RegistrationAttempt.reset_limits()
        
        if success:
            # Reset the Flask-Limiter limits
            try:
                limiter.reset()
                logger.info("Successfully reset Flask-Limiter rate limits")
            except Exception as e:
                logger.warning(f"Failed to reset Flask-Limiter limits: {str(e)}")
                # Continue anyway since we successfully reset registration attempts
            
            # Log the action
            log = SecurityLog(
                title='Rate Limits Reset',
                message=f'Admin {current_user.username} reset all rate limits',
                severity='medium',
                user_id=current_user.id
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Rate limits reset successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
            
    except Exception as e:
        error_msg = f"Error resetting rate limits: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500 