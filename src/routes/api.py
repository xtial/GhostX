from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.models import Campaign, CampaignStatus
from src.utils.rate_limiter import RateLimiter
from src.database import db
import logging

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

# Campaign endpoints
@api.route('/campaigns')
@login_required
def get_campaigns():
    try:
        campaigns = Campaign.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'campaigns': [{
                'id': c.id,
                'name': c.name,
                'status': c.status,
                'total_recipients': c.total_recipients,
                'emails_sent': c.emails_sent,
                'emails_delivered': c.emails_delivered,
                'emails_opened': c.emails_opened,
                'emails_clicked': c.emails_clicked,
                'emails_failed': c.emails_failed
            } for c in campaigns]
        })
    except Exception as e:
        logger.error(f"Error getting campaigns: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load campaigns'
        }), 500

@api.route('/campaigns', methods=['POST'])
@login_required
def create_campaign():
    try:
        data = request.get_json()
        campaign = Campaign(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description', ''),
            template_id=data['template_id'],
            is_ab_test=data.get('is_ab_test', False),
            template_b_id=data.get('template_b_id'),
            ab_test_ratio=data.get('ab_test_ratio', 0.5),
            schedule_time=data.get('schedule_time'),
            send_rate=data.get('send_rate', 10),
            total_recipients=data.get('total_recipients', 0),
            status=CampaignStatus.SCHEDULED.value if data.get('schedule_time') else CampaignStatus.DRAFT.value
        )
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'campaign_id': campaign.id
        })
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create campaign'
        }), 500

@api.route('/campaigns/<int:campaign_id>')
@login_required
def get_campaign(campaign_id):
    try:
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                'success': False,
                'message': 'Campaign not found'
            }), 404
            
        return jsonify({
            'success': True,
            'campaign': {
                'id': campaign.id,
                'name': campaign.name,
                'status': campaign.status,
                'total_recipients': campaign.total_recipients,
                'emails_sent': campaign.emails_sent,
                'emails_delivered': campaign.emails_delivered,
                'emails_opened': campaign.emails_opened,
                'emails_clicked': campaign.emails_clicked,
                'emails_failed': campaign.emails_failed,
                'stats': campaign.get_stats()
            }
        })
    except Exception as e:
        logger.error(f"Error getting campaign: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load campaign details'
        }), 500

@api.route('/campaigns/<int:campaign_id>/pause', methods=['POST'])
@login_required
def pause_campaign(campaign_id):
    try:
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                'success': False,
                'message': 'Campaign not found'
            }), 404
            
        if campaign.pause():
            return jsonify({'success': True})
        return jsonify({
            'success': False,
            'message': 'Campaign cannot be paused'
        }), 400
    except Exception as e:
        logger.error(f"Error pausing campaign: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to pause campaign'
        }), 500

@api.route('/campaigns/<int:campaign_id>/resume', methods=['POST'])
@login_required
def resume_campaign(campaign_id):
    try:
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                'success': False,
                'message': 'Campaign not found'
            }), 404
            
        if campaign.resume():
            return jsonify({'success': True})
        return jsonify({
            'success': False,
            'message': 'Campaign cannot be resumed'
        }), 400
    except Exception as e:
        logger.error(f"Error resuming campaign: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to resume campaign'
        }), 500

@api.route('/campaigns/<int:campaign_id>/stop', methods=['POST'])
@login_required
def stop_campaign(campaign_id):
    try:
        campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first()
        if not campaign:
            return jsonify({
                'success': False,
                'message': 'Campaign not found'
            }), 404
            
        if campaign.complete():
            return jsonify({'success': True})
        return jsonify({
            'success': False,
            'message': 'Campaign cannot be stopped'
        }), 400
    except Exception as e:
        logger.error(f"Error stopping campaign: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to stop campaign'
        }), 500

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