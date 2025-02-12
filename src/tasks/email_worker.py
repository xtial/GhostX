from datetime import datetime, timedelta
import threading
import time
import logging
from typing import List, Dict, Optional
from src import db
from src.models import Campaign, EmailTemplate, EmailTracking, User, CampaignStatus
from src.utils.email_sender import send_email
from src.utils.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

class EmailWorker:
    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.campaign_threads = {}
        self.lock = threading.Lock()
        
    def start(self):
        """Start the email worker"""
        with self.lock:
            if self.running:
                return
                
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_campaigns)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            logger.info("Email worker started")
        
    def stop(self):
        """Stop the email worker"""
        with self.lock:
            self.running = False
            if self.worker_thread:
                self.worker_thread.join()
            logger.info("Email worker stopped")
        
    def _process_campaigns(self):
        """Main worker loop for processing campaigns"""
        while self.running:
            try:
                # Get scheduled campaigns that should start
                campaigns = Campaign.query.filter(
                    Campaign.status == CampaignStatus.SCHEDULED.value,
                    Campaign.schedule_time <= datetime.utcnow()
                ).all()
                
                for campaign in campaigns:
                    if campaign.id not in self.campaign_threads:
                        thread = threading.Thread(
                            target=self._run_campaign,
                            args=(campaign,)
                        )
                        thread.daemon = True
                        thread.start()
                        self.campaign_threads[campaign.id] = thread
                
                # Clean up finished campaign threads
                with self.lock:
                    finished = []
                    for cid, thread in self.campaign_threads.items():
                        if not thread.is_alive():
                            finished.append(cid)
                    for cid in finished:
                        del self.campaign_threads[cid]
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in campaign processor: {str(e)}")
                time.sleep(60)  # Wait before retrying
                
    def _run_campaign(self, campaign: Campaign):
        """Run a single email campaign"""
        try:
            logger.info(f"Starting campaign {campaign.id}: {campaign.name}")
            campaign.start()
            
            # Get template(s)
            template_a = EmailTemplate.query.get(campaign.template_id)
            template_b = None
            if campaign.is_ab_test:
                template_b = EmailTemplate.query.get(campaign.template_b_id)
            
            # Process recipients in batches
            batch_size = min(campaign.send_rate, 50)  # Max 50 emails per batch
            offset = 0
            
            while (campaign.status == CampaignStatus.RUNNING.value and 
                   offset < campaign.total_recipients):
                batch = self._get_recipient_batch(campaign, offset, batch_size)
                if not batch:
                    break
                    
                for recipient in batch:
                    if campaign.status != CampaignStatus.RUNNING.value:
                        break
                        
                    try:
                        # Check rate limits
                        if not check_rate_limit(campaign.user_id):
                            logger.warning(f"Rate limit reached for user {campaign.user_id}")
                            time.sleep(3600)  # Wait an hour
                            continue
                        
                        # Select template for A/B testing
                        template = template_a
                        if campaign.is_ab_test:
                            if offset < (campaign.total_recipients * campaign.ab_test_ratio):
                                template = template_a
                            else:
                                template = template_b
                        
                        # Create tracking entry
                        tracking = EmailTracking(
                            campaign_id=campaign.id,
                            user_id=campaign.user_id,
                            recipient_email=recipient,
                            template_id=template.id
                        )
                        db.session.add(tracking)
                        db.session.commit()
                        
                        # Send email
                        success = send_email(
                            recipient_email=recipient,
                            template=template,
                            tracking_id=tracking.tracking_pixel_id
                        )
                        
                        # Update tracking and stats
                        if success:
                            tracking.track_event('sent')
                            campaign.emails_sent += 1
                            template.update_stats(success=True, opened=False, clicked=False)
                        else:
                            tracking.track_event('failed')
                            campaign.emails_failed += 1
                            template.update_stats(success=False, opened=False, clicked=False)
                        
                        db.session.commit()
                        
                        # Rate limiting sleep
                        sleep_time = 3600 / campaign.send_rate
                        time.sleep(sleep_time)  # Space out sends
                        
                    except Exception as e:
                        logger.error(f"Error sending campaign email: {str(e)}")
                        campaign.emails_failed += 1
                        db.session.commit()
                
                offset += batch_size
            
            # Complete campaign
            if campaign.status == CampaignStatus.RUNNING.value:
                campaign.complete()
                
            logger.info(f"Campaign {campaign.id} completed")
            
        except Exception as e:
            logger.error(f"Campaign {campaign.id} failed: {str(e)}")
            campaign.fail()
            
    def _get_recipient_batch(self, campaign: Campaign, offset: int, limit: int) -> List[str]:
        """Get a batch of recipients for a campaign"""
        try:
            # Query recipients from the database
            recipients = db.session.query(EmailTracking.recipient_email).\
                filter(EmailTracking.campaign_id == campaign.id).\
                offset(offset).limit(limit).all()
            
            return [r[0] for r in recipients]
            
        except Exception as e:
            logger.error(f"Error getting recipient batch: {str(e)}")
            return []

    def get_campaign_status(self, campaign_id: int) -> Optional[Dict]:
        """Get the current status of a campaign"""
        try:
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return None
                
            return {
                'id': campaign.id,
                'name': campaign.name,
                'status': campaign.status,
                'total_recipients': campaign.total_recipients,
                'emails_sent': campaign.emails_sent,
                'emails_delivered': campaign.emails_delivered,
                'emails_opened': campaign.emails_opened,
                'emails_clicked': campaign.emails_clicked,
                'emails_failed': campaign.emails_failed,
                'progress': (campaign.emails_sent / campaign.total_recipients * 100) 
                           if campaign.total_recipients > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign status: {str(e)}")
            return None

email_worker = EmailWorker() 