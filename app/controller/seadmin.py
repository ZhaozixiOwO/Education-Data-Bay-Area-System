import io
import traceback

from app.models.base import db
from app.models.datauser import DataUser
from app.models.eadmin import EAdmin
from app.models.oconvener import OConvener
from app.models.registrationapplication import RegistrationApplication
from app.models.tadmin import TAdmin
from flask import jsonify, Blueprint, request
from flask import send_file
from flask import url_for
from sqlalchemy import func

seadminBP = Blueprint('seadmin', __name__)


@seadminBP.route('/get-registration-applications', methods=['POST'])
def show_registration_applications():
  try:
    applications = RegistrationApplication.query.filter_by(status=2).all()
    result = []
    
    for app in applications:
      if app.proofDocuments:
        file_url = url_for('seadmin.download_proof', email=app.oconvenerEmail, _external=True)
      else:
        file_url = None
      
      result.append({
        "applicationId": app.applicationId,
        "organizationName": app.organizationName,
        "oconvenerEmail": app.oconvenerEmail,
        "proofDocuments": file_url,
      })
    
    return jsonify(result), 200
  except Exception as e:
    return jsonify({"error": "Failed to fetch applications"}), 500


@seadminBP.route('/download-proof/<email>', methods=['GET'])
def download_proof(email):
  if not email:
    return jsonify({'error': 'Lack of email'}), 400
  
  app_entry = RegistrationApplication.query.filter_by(oconvenerEmail=email.lower()).first()
  if not app_entry or not app_entry.proofDocuments:
    return jsonify({"code": "NOT_FOUND", "message": "No relevant documents were found"}), 404
  
  pdf_data = io.BytesIO(app_entry.proofDocuments)
  filename = f"{email}_proof_document.pdf"
  
  response = send_file(
    pdf_data,
    as_attachment=True,
    attachment_filename=filename,
    mimetype='application/pdf'
  )
  
  return response


@seadminBP.route('/approve-registration', methods=['POST'])
def approve_registration():
  try:
    data = request.get_json()
    app_id = data.get("applicationId")
    
    application = RegistrationApplication.query.filter_by(applicationId=app_id).first()
    
    if not application:
      return jsonify({"message": f"Application with ID {app_id} not found"}), 404
    
    if application.status != 2:
      return jsonify({"message": "Only applications with status 2 (pending) can be approved"}), 400
    
    if not application.organizationName:
      return jsonify({"message": "Organization name is required for username generation"}), 400
    
    generated_username = f"{application.organizationName.strip()}man"
    application.status = 3
    new_user_id = get_max_user_id() + 1
    
    new_oconvener = OConvener(
      userId=new_user_id,
      organizationName=application.organizationName,
      email=application.oconvenerEmail,
      userName=generated_username,
      accessLevel="OConvener",
      authcode=None
    )
    db.session.add(new_oconvener)
    
    try:
      db.session.commit()
    except Exception as e:
      traceback.print_exc()
      db.session.rollback()
      return jsonify({"message": "Database commit failed", "error": str(e)}), 500
    
    return jsonify({"message": f"Application {app_id} approved successfully"}), 200
  
  except Exception as e:
    return jsonify({"message": "Server error", "error": str(e)}), 500


@seadminBP.route('/reject-registration', methods=['POST'])
def reject_registration():
  try:
    data = request.get_json()
    if not data or 'applicationId' not in data:
      return jsonify({'message': 'The request format is incorrect and the applicationId is missing'}), 400
    
    app_id = data['applicationId']
    app = RegistrationApplication.query.filter_by(applicationId=app_id).first()
    
    if not app:
      return jsonify({'message': f'The registration application with ID {app_id} was not found'}), 404
    
    app.status = 0
    db.session.commit()
    
    return jsonify({
      'message': f'Successfully rejected the registration application {app_id}',
      'rejected': app_id
    }), 200
  
  except Exception as e:
    db.session.rollback()
    return jsonify({'message': 'An error occurred during the rejection process', 'error': str(e)}), 500


def get_max_user_id():
  max_ids = []
  
  try:

    datauser_max = db.session.query(func.max(DataUser.userId)).scalar()
    tadmin_max = db.session.query(func.max(TAdmin.userId)).scalar()
    eadmin_max = db.session.query(func.max(EAdmin.userId)).scalar()
    oconvener_max = db.session.query(func.max(OConvener.userId)).scalar()
    seadmin_max = db.session.query(func.max(OConvener.userId)).scalar()
    for val in [datauser_max, tadmin_max, eadmin_max, oconvener_max, seadmin_max]:
      if val is not None:
        max_ids.append(val)
    
    if not max_ids:
      return 0
    return max(max_ids)
  
  except Exception as e:
    return 0
