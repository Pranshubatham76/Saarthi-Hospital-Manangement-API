from flask import Blueprint, request, send_file, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import tempfile
import os
from app.services.reporting_service import reporting_service
from app.auth.decorators import admin_required, hospital_admin_or_admin_required
from app.utils.helpers import create_success_response, create_error_response
from app.services.cache_service import cached
import io

reporting_bp = Blueprint('reporting', __name__)


@reporting_bp.route('/hospital-statistics', methods=['GET'])
@jwt_required()
def get_hospital_statistics():
    """Generate hospital statistics report"""
    try:
        hospital_id = request.args.get('hospital_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Check permissions
        claims = get_jwt()
        user_role = claims.get('role')
        user_type = claims.get('type')
        current_user_id = get_jwt_identity()
        
        if user_role == 'hospital_admin' and user_type == 'hospital':
            # Hospital admins can only see their own hospital stats
            if hospital_id and hospital_id != current_user_id:
                return create_error_response('Access denied to other hospital data', status_code=403)
            hospital_id = current_user_id
        elif user_role not in ['admin']:
            return create_error_response('Admin or hospital admin access required', status_code=403)
        
        report_data = reporting_service.generate_hospital_statistics(
            hospital_id=hospital_id,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return create_success_response(
            'Hospital statistics generated successfully',
            report_data
        )
        
    except Exception as e:
        return create_error_response(f'Failed to generate hospital statistics: {str(e)}', status_code=500)


@reporting_bp.route('/user-activity', methods=['GET'])
@admin_required
def get_user_activity_report():
    """Generate user activity report"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_role = request.args.get('role')
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        report_data = reporting_service.generate_user_activity_report(
            start_date=start_dt,
            end_date=end_dt,
            user_role=user_role
        )
        
        return create_success_response(
            'User activity report generated successfully',
            report_data
        )
        
    except Exception as e:
        return create_error_response(f'Failed to generate user activity report: {str(e)}', status_code=500)


@reporting_bp.route('/export/csv', methods=['POST'])
@jwt_required()
def export_report_csv():
    """Export report data to CSV"""
    try:
        data = request.get_json()
        
        if not data or 'report_data' not in data:
            return create_error_response('Report data is required', status_code=400)
        
        csv_content = reporting_service.export_report_to_csv(data['report_data'])
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'hospital_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return create_error_response(f'Failed to export CSV: {str(e)}', status_code=500)


@reporting_bp.route('/export/excel', methods=['POST'])
@jwt_required()
def export_report_excel():
    """Export report data to Excel"""
    try:
        data = request.get_json()
        
        if not data or 'report_data' not in data:
            return create_error_response('Report data is required', status_code=400)
        
        excel_content = reporting_service.export_report_to_excel(data['report_data'])
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file.write(excel_content)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'hospital_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return create_error_response(f'Failed to export Excel: {str(e)}', status_code=500)


@reporting_bp.route('/export/pdf', methods=['POST'])
@jwt_required()
def export_report_pdf():
    """Export report data to PDF"""
    try:
        data = request.get_json()
        
        if not data or 'report_data' not in data:
            return create_error_response('Report data is required', status_code=400)
        
        pdf_content = reporting_service.export_report_to_pdf(data['report_data'])
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.write(pdf_content)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'hospital_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return create_error_response(f'Failed to export PDF: {str(e)}', status_code=500)


@reporting_bp.route('/dashboard-charts', methods=['GET'])
@jwt_required()
@cached(ttl=300, key_pattern="charts_{}_{}_{}")  # Cache for 5 minutes
def get_dashboard_charts():
    """Get dashboard charts data"""
    try:
        hospital_id = request.args.get('hospital_id', type=int)
        days = request.args.get('days', default=30, type=int)
        
        # Check permissions
        claims = get_jwt()
        user_role = claims.get('role')
        user_type = claims.get('type')
        current_user_id = get_jwt_identity()
        
        if user_role == 'hospital_admin' and user_type == 'hospital':
            hospital_id = current_user_id
        elif user_role not in ['admin'] and hospital_id:
            # Regular users can't access specific hospital charts
            return create_error_response('Access denied', status_code=403)
        
        charts_data = reporting_service.generate_dashboard_charts(
            hospital_id=hospital_id,
            days=days
        )
        
        return create_success_response(
            'Dashboard charts generated successfully',
            {'charts': charts_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to generate dashboard charts: {str(e)}', status_code=500)


@reporting_bp.route('/analytics/summary', methods=['GET'])
@admin_required
def get_analytics_summary():
    """Get analytics summary for admin dashboard"""
    try:
        days = request.args.get('days', default=7, type=int)
        
        # This could include various analytics
        summary_data = {
            'total_reports_generated': 150,  # This would be tracked in actual implementation
            'most_requested_report_type': 'hospital_statistics',
            'average_generation_time': '2.3s',
            'popular_export_formats': {
                'pdf': 45,
                'excel': 35,
                'csv': 20
            }
        }
        
        return create_success_response(
            'Analytics summary retrieved successfully',
            summary_data
        )
        
    except Exception as e:
        return create_error_response(f'Failed to get analytics summary: {str(e)}', status_code=500)


# Cleanup function for temporary files
@reporting_bp.after_request
def cleanup_temp_files(response):
    """Clean up temporary files after request"""
    # This would be implemented to clean up temporary export files
    # after they've been sent to the client
    return response
