import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import current_app, render_template_string
from datetime import datetime
from app.models import db, Notification
from app.utils.helpers import create_error_response, create_success_response
import logging


class EmailService:
    """Enhanced Email Service with template support and notifications"""
    
    def __init__(self):
        self.smtp_server = None
        self.smtp_port = None
        self.username = None
        self.password = None
        self.use_tls = True
        self.logger = logging.getLogger(__name__)
    
    def configure_from_app(self, app=None):
        """Configure email service from Flask app config"""
        if app is None:
            app = current_app
            
        self.smtp_server = app.config.get('MAIL_SERVER')
        self.smtp_port = app.config.get('MAIL_PORT', 587)
        self.username = app.config.get('MAIL_USERNAME')
        self.password = app.config.get('MAIL_PASSWORD')
        self.use_tls = app.config.get('MAIL_USE_TLS', True)
    
    def send_email(self, to_email, subject, body, html_body=None, attachments=None, cc=None, bcc=None):
        """Send email with optional HTML body and attachments"""
        try:
            if not self.smtp_server or not self.username:
                self.logger.error("Email service not properly configured")
                return False, "Email service not configured"
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            # Add plain text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    if os.path.isfile(attachment):
                        with open(attachment, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(attachment)}'
                            )
                            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            
            recipients = [to_email]
            if cc:
                recipients.extend(cc.split(','))
            if bcc:
                recipients.extend(bcc.split(','))
            
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            self.logger.info(f"Email sent successfully to {to_email}")
            return True, "Email sent successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False, f"Failed to send email: {str(e)}"
    
    def send_welcome_email(self, user_email, user_name, role="user"):
        """Send welcome email to new user"""
        subject = "Welcome to Hospital Management System"
        
        body = f"""
        Dear {user_name},

        Welcome to the Hospital Management System!

        Your account has been successfully created with the role: {role.title()}

        You can now access your account using your login credentials.

        If you have any questions, please contact our support team.

        Best regards,
        Hospital Management System Team
        """
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
                    <h1>Welcome to Hospital Management System</h1>
                </div>
                <div style="padding: 20px;">
                    <p>Dear <strong>{user_name}</strong>,</p>
                    <p>Welcome to the Hospital Management System!</p>
                    <p>Your account has been successfully created with the role: <strong>{role.title()}</strong></p>
                    <p>You can now access your account using your login credentials.</p>
                    <div style="background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-left: 4px solid #2c5aa0;">
                        <p><strong>Next Steps:</strong></p>
                        <ul>
                            <li>Login to your account</li>
                            <li>Complete your profile</li>
                            <li>Explore available features</li>
                        </ul>
                    </div>
                    <p>If you have any questions, please contact our support team.</p>
                    <p>Best regards,<br>Hospital Management System Team</p>
                </div>
                <div style="background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #666;">
                    <p>&copy; 2024 Hospital Management System. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def send_appointment_confirmation(self, user_email, user_name, appointment_details):
        """Send appointment confirmation email"""
        subject = "Appointment Confirmation - Hospital Management System"
        
        appointment_date = appointment_details.get('scheduled_time', 'Not specified')
        doctor_name = appointment_details.get('doctor_name', 'Not assigned')
        hospital_name = appointment_details.get('hospital_name', 'Not specified')
        appointment_id = appointment_details.get('id', 'N/A')
        
        body = f"""
        Dear {user_name},

        Your appointment has been confirmed!

        Appointment Details:
        - Appointment ID: {appointment_id}
        - Date & Time: {appointment_date}
        - Doctor: {doctor_name}
        - Hospital: {hospital_name}

        Please arrive 15 minutes before your scheduled time.

        Thank you for choosing our services.

        Best regards,
        Hospital Management System Team
        """
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #28a745; color: white; padding: 20px; text-align: center;">
                    <h1>🏥 Appointment Confirmed</h1>
                </div>
                <div style="padding: 20px;">
                    <p>Dear <strong>{user_name}</strong>,</p>
                    <p>Your appointment has been confirmed!</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px;">
                        <h3 style="color: #28a745; margin-top: 0;">📅 Appointment Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Appointment ID:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{appointment_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Date & Time:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{appointment_date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Doctor:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{doctor_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px;"><strong>Hospital:</strong></td>
                                <td style="padding: 8px;">{hospital_name}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107; border-radius: 5px;">
                        <p><strong>⏰ Important Reminder:</strong></p>
                        <p>Please arrive 15 minutes before your scheduled time.</p>
                    </div>
                    
                    <p>Thank you for choosing our services.</p>
                    <p>Best regards,<br>Hospital Management System Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def send_appointment_reminder(self, user_email, user_name, appointment_details):
        """Send appointment reminder email"""
        subject = "Appointment Reminder - Tomorrow"
        
        appointment_date = appointment_details.get('scheduled_time', 'Not specified')
        doctor_name = appointment_details.get('doctor_name', 'Not assigned')
        hospital_name = appointment_details.get('hospital_name', 'Not specified')
        
        body = f"""
        Dear {user_name},

        This is a friendly reminder about your appointment tomorrow.

        Appointment Details:
        - Date & Time: {appointment_date}
        - Doctor: {doctor_name}
        - Hospital: {hospital_name}

        Please don't forget to bring any relevant medical documents.

        Best regards,
        Hospital Management System Team
        """
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #ffc107; color: #212529; padding: 20px; text-align: center;">
                    <h1>⏰ Appointment Reminder</h1>
                </div>
                <div style="padding: 20px;">
                    <p>Dear <strong>{user_name}</strong>,</p>
                    <p>This is a friendly reminder about your appointment <strong>tomorrow</strong>.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px;">
                        <h3 style="color: #ffc107; margin-top: 0;">📅 Appointment Details</h3>
                        <p><strong>Date & Time:</strong> {appointment_date}</p>
                        <p><strong>Doctor:</strong> {doctor_name}</p>
                        <p><strong>Hospital:</strong> {hospital_name}</p>
                    </div>
                    
                    <div style="background-color: #d1ecf1; padding: 15px; margin: 20px 0; border-left: 4px solid #17a2b8; border-radius: 5px;">
                        <p><strong>📋 Don't forget to bring:</strong></p>
                        <ul>
                            <li>Valid ID</li>
                            <li>Previous medical records</li>
                            <li>Insurance information</li>
                            <li>List of current medications</li>
                        </ul>
                    </div>
                    
                    <p>Best regards,<br>Hospital Management System Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def send_emergency_alert(self, recipient_emails, emergency_details):
        """Send emergency alert to relevant personnel"""
        subject = f"🚨 EMERGENCY ALERT - {emergency_details.get('emergency_type', 'Unknown')}"
        
        location = emergency_details.get('location', 'Not specified')
        contact = emergency_details.get('contact_number', 'Not provided')
        details = emergency_details.get('details', 'No additional details')
        emergency_id = emergency_details.get('id', 'N/A')
        
        body = f"""
        EMERGENCY ALERT
        
        Emergency ID: {emergency_id}
        Type: {emergency_details.get('emergency_type', 'Unknown')}
        Location: {location}
        Contact: {contact}
        Details: {details}
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Please respond immediately.
        
        Hospital Management System
        """
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center;">
                    <h1>🚨 EMERGENCY ALERT</h1>
                    <h2>{emergency_details.get('emergency_type', 'Unknown').upper()}</h2>
                </div>
                <div style="padding: 20px; background-color: #f8d7da; border: 2px solid #dc3545;">
                    <div style="background-color: white; padding: 20px; border-radius: 5px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Emergency ID:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{emergency_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Type:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{emergency_details.get('emergency_type', 'Unknown')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Location:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{location}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Contact:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{contact}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Time:</strong></td>
                                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px;"><strong>Details:</strong></td>
                                <td style="padding: 8px;">{details}</td>
                            </tr>
                        </table>
                    </div>
                    <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #721c24; color: white; border-radius: 5px;">
                        <strong>⚡ PLEASE RESPOND IMMEDIATELY ⚡</strong>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send to multiple recipients
        results = []
        for email in recipient_emails:
            result = self.send_email(email.strip(), subject, body, html_body)
            results.append((email, result))
        
        return results
    
    def send_password_reset(self, user_email, user_name, reset_token):
        """Send password reset email"""
        subject = "Password Reset Request - Hospital Management System"
        reset_link = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        body = f"""
        Dear {user_name},

        You have requested to reset your password for Hospital Management System.

        Please click on the following link to reset your password:
        {reset_link}

        This link will expire in 1 hour for security reasons.

        If you did not request this password reset, please ignore this email.

        Best regards,
        Hospital Management System Team
        """
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #6f42c1; color: white; padding: 20px; text-align: center;">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div style="padding: 20px;">
                    <p>Dear <strong>{user_name}</strong>,</p>
                    <p>You have requested to reset your password for Hospital Management System.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #6f42c1; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107; border-radius: 5px;">
                        <p><strong>⏰ Important:</strong></p>
                        <p>This link will expire in <strong>1 hour</strong> for security reasons.</p>
                    </div>
                    
                    <p>If you did not request this password reset, please ignore this email.</p>
                    <p>Best regards,<br>Hospital Management System Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body, html_body)
    
    def create_notification(self, user_id, title, body, metadata=None):
        """Create in-app notification"""
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                body=body,
                metadata=metadata or {},
                read=False
            )
            db.session.add(notification)
            db.session.commit()
            return True, "Notification created successfully"
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Failed to create notification: {str(e)}")
            return False, f"Failed to create notification: {str(e)}"
    
    def send_notification_and_email(self, user_email, user_id, user_name, subject, email_body, html_body=None, notification_metadata=None):
        """Send both email and in-app notification"""
        # Send email
        email_result = self.send_email(user_email, subject, email_body, html_body)
        
        # Create in-app notification
        notification_result = self.create_notification(
            user_id=user_id,
            title=subject,
            body=email_body[:500],  # Truncate for notification
            metadata=notification_metadata
        )
        
        return {
            'email': email_result,
            'notification': notification_result
        }


# Global email service instance
email_service = EmailService()


def init_email_service(app):
    """Initialize email service with app configuration"""
    email_service.configure_from_app(app)
