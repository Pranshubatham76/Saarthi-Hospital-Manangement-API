from datetime import datetime, timedelta
from sqlalchemy import func, text, desc, asc, and_, or_
from flask import current_app
import json
import csv
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import xlsxwriter
from app.models import *
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import logging


class ReportingService:
    """Comprehensive reporting and analytics service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_hospital_statistics(self, hospital_id=None, start_date=None, end_date=None):
        """Generate comprehensive hospital statistics"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Build base query
            query_filter = []
            if hospital_id:
                query_filter.append(Hospital.id == hospital_id)
            
            # Basic hospital metrics
            hospitals_query = Hospital.query
            if hospital_id:
                hospitals_query = hospitals_query.filter(Hospital.id == hospital_id)
            
            hospitals = hospitals_query.all()
            
            report_data = {
                'generated_at': datetime.utcnow().isoformat(),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'hospitals': []
            }
            
            for hospital in hospitals:
                hospital_stats = {
                    'hospital_id': hospital.id,
                    'name': hospital.name,
                    'location': hospital.location,
                    'type': hospital.hospital_type,
                    'bed_availability': hospital.bedAvailability,
                    'opd_status': hospital.opd_status.value if hospital.opd_status else None,
                    'total_floors': hospital.floors.count(),
                    'total_wards': sum(floor.wards.count() for floor in hospital.floors),
                    'total_beds': self._count_hospital_beds(hospital),
                    'bed_occupancy': self._calculate_bed_occupancy(hospital),
                    'appointments': self._get_appointment_stats(hospital.id, start_date, end_date),
                    'emergency_cases': self._get_emergency_stats(hospital.id, start_date, end_date),
                    'blood_requests': self._get_blood_request_stats(hospital.id, start_date, end_date),
                    'monthly_trends': self._get_monthly_trends(hospital.id, start_date, end_date)
                }
                report_data['hospitals'].append(hospital_stats)
            
            # System-wide statistics
            if not hospital_id:
                report_data['system_wide'] = self._get_system_wide_stats(start_date, end_date)
            
            return report_data
            
        except Exception as e:
            self.logger.error(f"Error generating hospital statistics: {str(e)}")
            raise
    
    def _count_hospital_beds(self, hospital):
        """Count total beds in a hospital"""
        total_beds = 0
        for floor in hospital.floors:
            for ward in floor.wards:
                total_beds += ward.beds.count()
        return total_beds
    
    def _calculate_bed_occupancy(self, hospital):
        """Calculate bed occupancy percentage"""
        total_beds = self._count_hospital_beds(hospital)
        if total_beds == 0:
            return 0
        
        occupied_beds = 0
        for floor in hospital.floors:
            for ward in floor.wards:
                occupied_beds += ward.beds.filter(Bed.status == BedStatus.OCCUPIED).count()
        
        return round((occupied_beds / total_beds) * 100, 2)
    
    def _get_appointment_stats(self, hospital_id, start_date, end_date):
        """Get appointment statistics for a hospital"""
        appointments = Appointment.query.filter(
            Appointment.hospital_id == hospital_id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        )
        
        total_appointments = appointments.count()
        confirmed = appointments.filter(Appointment.status == AppointmentStatus.CONFIRMED).count()
        completed = appointments.filter(Appointment.status == AppointmentStatus.COMPLETED).count()
        cancelled = appointments.filter(Appointment.status == AppointmentStatus.CANCELLED).count()
        no_show = appointments.filter(Appointment.status == AppointmentStatus.NO_SHOW).count()
        
        # Daily appointment trends
        daily_trends = db.session.query(
            func.date(Appointment.created_at).label('date'),
            func.count(Appointment.id).label('count')
        ).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        ).group_by(func.date(Appointment.created_at)).all()
        
        return {
            'total': total_appointments,
            'confirmed': confirmed,
            'completed': completed,
            'cancelled': cancelled,
            'no_show': no_show,
            'completion_rate': round((completed / total_appointments * 100) if total_appointments > 0 else 0, 2),
            'daily_trends': [{'date': trend.date.isoformat(), 'count': trend.count} for trend in daily_trends]
        }
    
    def _get_emergency_stats(self, hospital_id, start_date, end_date):
        """Get emergency statistics for a hospital"""
        emergencies = Emergency.query.filter(
            Emergency.hospital_id == hospital_id,
            Emergency.created_at >= start_date,
            Emergency.created_at <= end_date
        )
        
        total_emergencies = emergencies.count()
        pending = emergencies.filter(Emergency.forward_status == 'Pending').count()
        resolved = emergencies.filter(Emergency.forward_status == 'Resolved').count()
        
        # Emergency types breakdown
        emergency_types = db.session.query(
            Emergency.emergency_type,
            func.count(Emergency.id).label('count')
        ).filter(
            Emergency.hospital_id == hospital_id,
            Emergency.created_at >= start_date,
            Emergency.created_at <= end_date
        ).group_by(Emergency.emergency_type).all()
        
        return {
            'total': total_emergencies,
            'pending': pending,
            'resolved': resolved,
            'resolution_rate': round((resolved / total_emergencies * 100) if total_emergencies > 0 else 0, 2),
            'types_breakdown': [{'type': et.emergency_type, 'count': et.count} for et in emergency_types]
        }
    
    def _get_blood_request_stats(self, hospital_id, start_date, end_date):
        """Get blood request statistics for a hospital"""
        # Get blood banks associated with this hospital
        blood_requests = ReserveBlood.query.join(BloodBank).join(bloodbank_hospital).filter(
            bloodbank_hospital.c.hospital_id == hospital_id,
            ReserveBlood.created_at >= start_date,
            ReserveBlood.created_at <= end_date
        )
        
        total_requests = blood_requests.count()
        pending = blood_requests.filter(ReserveBlood.status == StatusEnum.PENDING).count()
        resolved = blood_requests.filter(ReserveBlood.status == StatusEnum.RESOLVED).count()
        
        # Blood group breakdown
        blood_group_breakdown = db.session.query(
            ReserveBlood.blood_group,
            func.count(ReserveBlood.id).label('count')
        ).join(BloodBank).join(bloodbank_hospital).filter(
            bloodbank_hospital.c.hospital_id == hospital_id,
            ReserveBlood.created_at >= start_date,
            ReserveBlood.created_at <= end_date
        ).group_by(ReserveBlood.blood_group).all()
        
        return {
            'total': total_requests,
            'pending': pending,
            'resolved': resolved,
            'fulfillment_rate': round((resolved / total_requests * 100) if total_requests > 0 else 0, 2),
            'blood_group_breakdown': [{'blood_group': bg.blood_group, 'count': bg.count} for bg in blood_group_breakdown]
        }
    
    def _get_monthly_trends(self, hospital_id, start_date, end_date):
        """Get monthly trends for key metrics"""
        monthly_appointments = db.session.query(
            func.date_trunc('month', Appointment.created_at).label('month'),
            func.count(Appointment.id).label('appointments')
        ).filter(
            Appointment.hospital_id == hospital_id,
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        ).group_by(func.date_trunc('month', Appointment.created_at)).all()
        
        monthly_emergencies = db.session.query(
            func.date_trunc('month', Emergency.created_at).label('month'),
            func.count(Emergency.id).label('emergencies')
        ).filter(
            Emergency.hospital_id == hospital_id,
            Emergency.created_at >= start_date,
            Emergency.created_at <= end_date
        ).group_by(func.date_trunc('month', Emergency.created_at)).all()
        
        trends = []
        for ma in monthly_appointments:
            emergency_count = 0
            for me in monthly_emergencies:
                if me.month == ma.month:
                    emergency_count = me.emergencies
                    break
            
            trends.append({
                'month': ma.month.isoformat(),
                'appointments': ma.appointments,
                'emergencies': emergency_count
            })
        
        return trends
    
    def _get_system_wide_stats(self, start_date, end_date):
        """Get system-wide statistics"""
        return {
            'total_users': Users.query.count(),
            'new_users': Users.query.filter(
                Users.created_at >= start_date,
                Users.created_at <= end_date
            ).count(),
            'total_hospitals': Hospital.query.count(),
            'total_doctors': Doctors_Info.query.count(),
            'total_blood_banks': BloodBank.query.count(),
            'user_role_distribution': self._get_user_role_distribution(),
            'hospital_type_distribution': self._get_hospital_type_distribution(),
            'geographic_distribution': self._get_geographic_distribution()
        }
    
    def _get_user_role_distribution(self):
        """Get distribution of users by role"""
        role_distribution = db.session.query(
            Users.role,
            func.count(Users.id).label('count')
        ).group_by(Users.role).all()
        
        return [{'role': rd.role, 'count': rd.count} for rd in role_distribution]
    
    def _get_hospital_type_distribution(self):
        """Get distribution of hospitals by type"""
        type_distribution = db.session.query(
            Hospital.hospital_type,
            func.count(Hospital.id).label('count')
        ).group_by(Hospital.hospital_type).all()
        
        return [{'type': td.hospital_type or 'Unknown', 'count': td.count} for td in type_distribution]
    
    def _get_geographic_distribution(self):
        """Get geographic distribution of hospitals"""
        geo_distribution = db.session.query(
            Hospital.location,
            func.count(Hospital.id).label('count')
        ).group_by(Hospital.location).all()
        
        return [{'location': gd.location or 'Unknown', 'count': gd.count} for gd in geo_distribution]
    
    def generate_user_activity_report(self, start_date=None, end_date=None, user_role=None):
        """Generate user activity report"""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            query = Users.query
            if user_role:
                query = query.filter(Users.role == user_role)
            
            users = query.all()
            
            report_data = {
                'generated_at': datetime.utcnow().isoformat(),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'filter': {'role': user_role} if user_role else {},
                'summary': {
                    'total_users': len(users),
                    'active_users': self._count_active_users(users, start_date, end_date),
                    'new_registrations': self._count_new_registrations(start_date, end_date, user_role)
                },
                'users': []
            }
            
            for user in users[:100]:  # Limit to 100 users for performance
                user_activity = {
                    'user_id': user.id,
                    'username': user.username,
                    'fullname': user.fullname,
                    'email': user.email,
                    'role': user.role,
                    'created_at': user.created_at.isoformat(),
                    'activity': {
                        'appointments_made': user.appointments.filter(
                            Appointment.created_at >= start_date,
                            Appointment.created_at <= end_date
                        ).count(),
                        'emergencies_logged': user.emergencies.filter(
                            Emergency.created_at >= start_date,
                            Emergency.created_at <= end_date
                        ).count(),
                        'blood_requests': user.blood_requests.filter(
                            ReserveBlood.created_at >= start_date,
                            ReserveBlood.created_at <= end_date
                        ).count()
                    }
                }
                report_data['users'].append(user_activity)
            
            return report_data
            
        except Exception as e:
            self.logger.error(f"Error generating user activity report: {str(e)}")
            raise
    
    def _count_active_users(self, users, start_date, end_date):
        """Count users with activity in the date range"""
        active_count = 0
        for user in users:
            has_activity = (
                user.appointments.filter(
                    Appointment.created_at >= start_date,
                    Appointment.created_at <= end_date
                ).count() > 0 or
                user.emergencies.filter(
                    Emergency.created_at >= start_date,
                    Emergency.created_at <= end_date
                ).count() > 0 or
                user.blood_requests.filter(
                    ReserveBlood.created_at >= start_date,
                    ReserveBlood.created_at <= end_date
                ).count() > 0
            )
            if has_activity:
                active_count += 1
        return active_count
    
    def _count_new_registrations(self, start_date, end_date, user_role=None):
        """Count new user registrations in date range"""
        query = Users.query.filter(
            Users.created_at >= start_date,
            Users.created_at <= end_date
        )
        if user_role:
            query = query.filter(Users.role == user_role)
        
        return query.count()
    
    def export_report_to_csv(self, report_data):
        """Export report data to CSV format"""
        try:
            output = io.StringIO()
            
            # Write summary information
            writer = csv.writer(output)
            writer.writerow(['Hospital Management System Report'])
            writer.writerow(['Generated At:', report_data.get('generated_at', '')])
            writer.writerow([''])
            
            # Write hospital data if present
            if 'hospitals' in report_data:
                writer.writerow(['Hospital Statistics'])
                writer.writerow(['Hospital Name', 'Location', 'Type', 'Total Beds', 'Bed Occupancy %', 
                               'Total Appointments', 'Completion Rate %', 'Total Emergencies', 'Resolution Rate %'])
                
                for hospital in report_data['hospitals']:
                    writer.writerow([
                        hospital['name'],
                        hospital['location'],
                        hospital['type'],
                        hospital['total_beds'],
                        hospital['bed_occupancy'],
                        hospital['appointments']['total'],
                        hospital['appointments']['completion_rate'],
                        hospital['emergency_cases']['total'],
                        hospital['emergency_cases']['resolution_rate']
                    ])
            
            # Write user data if present
            if 'users' in report_data:
                writer.writerow([''])
                writer.writerow(['User Activity Report'])
                writer.writerow(['Username', 'Full Name', 'Email', 'Role', 'Registration Date', 
                               'Appointments Made', 'Emergencies Logged', 'Blood Requests'])
                
                for user in report_data['users']:
                    writer.writerow([
                        user['username'],
                        user['fullname'],
                        user['email'],
                        user['role'],
                        user['created_at'],
                        user['activity']['appointments_made'],
                        user['activity']['emergencies_logged'],
                        user['activity']['blood_requests']
                    ])
            
            csv_content = output.getvalue()
            output.close()
            return csv_content
            
        except Exception as e:
            self.logger.error(f"Error exporting report to CSV: {str(e)}")
            raise
    
    def export_report_to_excel(self, report_data):
        """Export report data to Excel format"""
        try:
            output = io.BytesIO()
            
            with xlsxwriter.Workbook(output, {'in_memory': True}) as workbook:
                # Create formats
                header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
                title_format = workbook.add_format({'bold': True, 'font_size': 16})
                
                # Create summary sheet
                summary_sheet = workbook.add_worksheet('Summary')
                summary_sheet.write('A1', 'Hospital Management System Report', title_format)
                summary_sheet.write('A2', 'Generated At:')
                summary_sheet.write('B2', report_data.get('generated_at', ''))
                
                row = 4
                
                # Add hospital data if present
                if 'hospitals' in report_data:
                    summary_sheet.write(f'A{row}', 'Hospital Statistics', header_format)
                    row += 1
                    
                    # Headers
                    headers = ['Hospital Name', 'Location', 'Type', 'Total Beds', 'Bed Occupancy %', 
                              'Total Appointments', 'Completion Rate %', 'Total Emergencies', 'Resolution Rate %']
                    for col, header in enumerate(headers):
                        summary_sheet.write(row, col, header, header_format)
                    row += 1
                    
                    # Data
                    for hospital in report_data['hospitals']:
                        data = [
                            hospital['name'],
                            hospital['location'],
                            hospital['type'],
                            hospital['total_beds'],
                            hospital['bed_occupancy'],
                            hospital['appointments']['total'],
                            hospital['appointments']['completion_rate'],
                            hospital['emergency_cases']['total'],
                            hospital['emergency_cases']['resolution_rate']
                        ]
                        for col, value in enumerate(data):
                            summary_sheet.write(row, col, value)
                        row += 1
                
                # Add user data if present
                if 'users' in report_data:
                    user_sheet = workbook.add_worksheet('User Activity')
                    user_sheet.write('A1', 'User Activity Report', title_format)
                    
                    # Headers
                    headers = ['Username', 'Full Name', 'Email', 'Role', 'Registration Date', 
                              'Appointments Made', 'Emergencies Logged', 'Blood Requests']
                    for col, header in enumerate(headers):
                        user_sheet.write(2, col, header, header_format)
                    
                    # Data
                    for row_idx, user in enumerate(report_data['users'], 3):
                        data = [
                            user['username'],
                            user['fullname'],
                            user['email'],
                            user['role'],
                            user['created_at'],
                            user['activity']['appointments_made'],
                            user['activity']['emergencies_logged'],
                            user['activity']['blood_requests']
                        ]
                        for col, value in enumerate(data):
                            user_sheet.write(row_idx, col, value)
            
            output.seek(0)
            return output.read()
            
        except Exception as e:
            self.logger.error(f"Error exporting report to Excel: {str(e)}")
            raise
    
    def export_report_to_pdf(self, report_data):
        """Export report data to PDF format"""
        try:
            output = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(output, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("Hospital Management System Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Generation info
            gen_info = Paragraph(f"Generated At: {report_data.get('generated_at', '')}", styles['Normal'])
            story.append(gen_info)
            story.append(Spacer(1, 12))
            
            # Hospital statistics if present
            if 'hospitals' in report_data:
                hospital_title = Paragraph("Hospital Statistics", styles['Heading2'])
                story.append(hospital_title)
                story.append(Spacer(1, 6))
                
                # Create table data
                table_data = [['Hospital Name', 'Location', 'Type', 'Total Beds', 'Bed Occupancy %']]
                
                for hospital in report_data['hospitals']:
                    table_data.append([
                        hospital['name'],
                        hospital['location'],
                        hospital['type'],
                        str(hospital['total_beds']),
                        f"{hospital['bed_occupancy']}%"
                    ])
                
                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
                story.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(story)
            output.seek(0)
            return output.read()
            
        except Exception as e:
            self.logger.error(f"Error exporting report to PDF: {str(e)}")
            raise
    
    def generate_dashboard_charts(self, hospital_id=None, days=30):
        """Generate dashboard charts data"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Set up matplotlib
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            charts = {}
            
            # Appointment trends chart
            appointments_data = self._get_appointment_trends_data(hospital_id, start_date, end_date)
            if appointments_data:
                charts['appointment_trends'] = self._create_line_chart(
                    appointments_data, 
                    'Appointment Trends', 
                    'Date', 
                    'Number of Appointments'
                )
            
            # Emergency types pie chart
            emergency_types_data = self._get_emergency_types_data(hospital_id, start_date, end_date)
            if emergency_types_data:
                charts['emergency_types'] = self._create_pie_chart(
                    emergency_types_data, 
                    'Emergency Types Distribution'
                )
            
            # Bed occupancy chart
            if hospital_id:
                occupancy_data = self._get_bed_occupancy_data(hospital_id)
                if occupancy_data:
                    charts['bed_occupancy'] = self._create_bar_chart(
                        occupancy_data, 
                        'Bed Occupancy by Ward', 
                        'Ward', 
                        'Occupancy %'
                    )
            
            return charts
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard charts: {str(e)}")
            return {}
    
    def _get_appointment_trends_data(self, hospital_id, start_date, end_date):
        """Get appointment trends data for charts"""
        query = db.session.query(
            func.date(Appointment.created_at).label('date'),
            func.count(Appointment.id).label('count')
        ).filter(
            Appointment.created_at >= start_date,
            Appointment.created_at <= end_date
        )
        
        if hospital_id:
            query = query.filter(Appointment.hospital_id == hospital_id)
        
        trends = query.group_by(func.date(Appointment.created_at)).all()
        
        return {
            'dates': [trend.date.strftime('%Y-%m-%d') for trend in trends],
            'counts': [trend.count for trend in trends]
        }
    
    def _get_emergency_types_data(self, hospital_id, start_date, end_date):
        """Get emergency types data for charts"""
        query = db.session.query(
            Emergency.emergency_type,
            func.count(Emergency.id).label('count')
        ).filter(
            Emergency.created_at >= start_date,
            Emergency.created_at <= end_date
        )
        
        if hospital_id:
            query = query.filter(Emergency.hospital_id == hospital_id)
        
        types = query.group_by(Emergency.emergency_type).all()
        
        return {
            'labels': [et.emergency_type for et in types],
            'values': [et.count for et in types]
        }
    
    def _get_bed_occupancy_data(self, hospital_id):
        """Get bed occupancy data for charts"""
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return None
        
        ward_data = []
        for floor in hospital.floors:
            for ward in floor.wards:
                total_beds = ward.beds.count()
                occupied_beds = ward.beds.filter(Bed.status == BedStatus.OCCUPIED).count()
                occupancy = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
                
                ward_data.append({
                    'ward': f"{ward.ward_number} ({ward.category.name if ward.category else 'General'})",
                    'occupancy': occupancy
                })
        
        return {
            'labels': [wd['ward'] for wd in ward_data],
            'values': [wd['occupancy'] for wd in ward_data]
        }
    
    def _create_line_chart(self, data, title, xlabel, ylabel):
        """Create line chart and return base64 encoded image"""
        try:
            plt.figure(figsize=(10, 6))
            plt.plot(data['dates'], data['counts'], marker='o', linewidth=2, markersize=6)
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            self.logger.error(f"Error creating line chart: {str(e)}")
            return None
    
    def _create_pie_chart(self, data, title):
        """Create pie chart and return base64 encoded image"""
        try:
            plt.figure(figsize=(8, 8))
            plt.pie(data['values'], labels=data['labels'], autopct='%1.1f%%', startangle=90)
            plt.title(title, fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            self.logger.error(f"Error creating pie chart: {str(e)}")
            return None
    
    def _create_bar_chart(self, data, title, xlabel, ylabel):
        """Create bar chart and return base64 encoded image"""
        try:
            plt.figure(figsize=(12, 6))
            bars = plt.bar(data['labels'], data['values'])
            plt.title(title, fontsize=16, fontweight='bold')
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{height:.1f}%', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            self.logger.error(f"Error creating bar chart: {str(e)}")
            return None


# Global reporting service instance
reporting_service = ReportingService()
