from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.utils.rate_limiter import RateLimiter
from src.database import db
import logging

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

# Quota endpoints
@api.route('/quota')
@login_required
def get_quota():
    try:
        quota = RateLimiter.get_remaining_quota(current_user.id)
        if not quota:
            return jsonify({
                'success': False,
                'message': 'Failed to get quota information'
            }), 500
            
        return jsonify({
            'success': True,
            'quota': quota
        })
    except Exception as e:
        logger.error(f"Error getting quota: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to get quota information'
        }), 500 