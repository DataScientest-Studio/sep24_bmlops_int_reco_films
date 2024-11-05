import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import logging
import os
from typing import Optional, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, config: Dict):
        self.config = config
        self.email_config = config.get('email', {})
        self.slack_config = config.get('slack', {})
        
    def send_email(
        self,
        subject: str,
        body: str,
        recipients: List[str],
        attachments: Optional[Dict[str, str]] = None
    ) -> bool:
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('sender')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if any
            if attachments:
                for filename, content in attachments.items():
                    attachment = MIMEText(content)
                    attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=filename
                    )
                    msg.attach(attachment)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(
                self.email_config.get('smtp_server'),
                self.email_config.get('smtp_port', 587)
            ) as server:
                server.starttls()
                server.login(
                    self.email_config.get('username'),
                    self.email_config.get('password')
                )
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
            
    def send_slack_message(
        self,
        message: str,
        channel: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """Send Slack notification."""
        try:
            webhook_url = self.slack_config.get('webhook_url')
            if not webhook_url:
                logger.error("Slack webhook URL not configured")
                return False
                
            payload = {
                'text': message,
                'channel': channel or self.slack_config.get('default_channel'),
                'username': self.slack_config.get('bot_name', 'MLOps Bot'),
                'icon_emoji': self.slack_config.get('bot_icon', ':robot_face:')
            }
            
            if attachments:
                payload['attachments'] = attachments
                
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Slack message sent successfully to {payload['channel']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Slack message: {str(e)}")
            return False
            
    def send_model_performance_alert(
        self,
        metrics: Dict[str, float],
        threshold: float,
        model_path: str
    ):
        """Send alert when model performance drops below threshold."""
        if metrics.get('rmse', float('inf')) > threshold:
            subject = "⚠️ Model Performance Alert"
            body = f"""
            Model performance has dropped below threshold:
            
            Current RMSE: {metrics.get('rmse', 'N/A')}
            Threshold: {threshold}
            Model Path: {model_path}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please investigate and take necessary action.
            """
            
            # Send email alert
            self.send_email(
                subject=subject,
                body=body,
                recipients=self.email_config.get('alert_recipients', [])
            )
            
            # Send Slack alert
            self.send_slack_message(
                message=subject,
                attachments=[{
                    'color': '#ff0000',
                    'text': body,
                    'fields': [
                        {
                            'title': 'RMSE',
                            'value': f"{metrics.get('rmse', 'N/A'):.4f}",
                            'short': True
                        },
                        {
                            'title': 'Threshold',
                            'value': f"{threshold:.4f}",
                            'short': True
                        }
                    ]
                }]
            )
            
    def send_data_drift_alert(
        self,
        drift_metrics: Dict[str, float],
        threshold: float
    ):
        """Send alert when data drift exceeds threshold."""
        if drift_metrics.get('drift_score', 0) > threshold:
            subject = "📊 Data Drift Alert"
            body = f"""
            Data drift detected above threshold:
            
            Drift Score: {drift_metrics.get('drift_score', 'N/A')}
            Threshold: {threshold}
            Affected Features: {', '.join(drift_metrics.get('drifted_features', []))}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Please review the data distribution changes.
            """
            
            # Send notifications
            self.send_email(
                subject=subject,
                body=body,
                recipients=self.email_config.get('alert_recipients', [])
            )
            
            self.send_slack_message(
                message=subject,
                attachments=[{
                    'color': '#ffa500',
                    'text': body,
                    'fields': [
                        {
                            'title': 'Drift Score',
                            'value': f"{drift_metrics.get('drift_score', 'N/A'):.4f}",
                            'short': True
                        },
                        {
                            'title': 'Threshold',
                            'value': f"{threshold:.4f}",
                            'short': True
                        }
                    ]
                }]
            ) 