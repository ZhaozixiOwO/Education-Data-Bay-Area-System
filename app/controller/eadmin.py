import io
import os
import re

import requests
from app.models.bankaccount import BankAccount
from app.models.base import db
from app.models.eadmin import EAdmin
from app.models.policy import Policy
from app.models.registrationapplication import RegistrationApplication
from flask import Blueprint, request, jsonify, send_file
from flask import url_for, current_app

eadminBP = Blueprint('eadmin', __name__)


@eadminBP.route('/get-membership-fee', methods=['POST'])
def get_membershipFee():
  try:
    eadmin = db.session.query(EAdmin).filter_by(status=1).first()
    if not eadmin:
      return jsonify({"error": "EAdmin not found"}), 404
    
    return jsonify({"success": True, "membershipFee": eadmin.membershipFee}), 200
  except Exception as e:
    return jsonify({"error": f"Error: {str(e)}"}), 500


@eadminBP.route('/set-membership-fee', methods=['POST'])
def set_membershipFee():
  try:
    userId = request.json.get('userId')
    membership_fee = request.json.get('membershipFee')
    
    if not userId or membership_fee is None:
      return jsonify({"error": "eadminId and membershipFee are required"}), 400

    eadmin = db.session.query(EAdmin).filter_by(userId=userId).first()
    if not eadmin:
      return jsonify({"error": "EAdmin not found"}), 404
    
    eadmin.membershipFee = membership_fee
    db.session.commit()
    
    return jsonify({"success": True, "message": "Membership fee updated successfully"}), 200
  
  except Exception as e:
    db.session.rollback()
    return jsonify({"error": f"Error: {str(e)}"}), 500


@eadminBP.route('/add_policy', methods=['POST'])
def add_policy():
  if 'file' not in request.files:
    return jsonify({"error": "There is no file section."}), 400
  
  file = request.files['file']
  title = request.form.get('title')
  
  if file.filename == '':
    return jsonify({"error": "Unselected file"}), 400
  
  if file and file.filename.endswith('.pdf'):

    file_data = file.read()
    
    new_policy = Policy(title=title, file_data=file_data)
    db.session.add(new_policy)
    db.session.commit()
    
    return jsonify({"message": "The policy document has been uploaded successfully", "policy_id": new_policy.policyId}), 200
  else:
    return jsonify({"error": "Only PDF files are allowed to be uploaded"}), 400


@eadminBP.route('/list_policies', methods=['GET'])
def list_policies():
  policies = Policy.query.all()
  return jsonify([{"id": p.policyId, "title": p.title} for p in policies])


@eadminBP.route('/delete_policy', methods=['POST'])
def delete_policy():
  policy_id = request.form.get('policyId')
  if not policy_id:
    return jsonify({'error': 'Lack of policyId'}), 400
  
  policy = Policy.query.get(policy_id)
  if not policy:
    return jsonify({'error': 'file does not exist'}), 404
  
  db.session.delete(policy)
  db.session.commit()
  return jsonify({'message': f'{policy.title} have deleted'}), 200


@eadminBP.route('/view_policy', methods=['POST'])
def view_policy():
  policy_id = request.form.get('policyId')
  if not policy_id:
    return jsonify({'error': 'Lack of policyId'}), 400
  
  policy = Policy.query.get(policy_id)
  if not policy:
    return jsonify({'error': 'file does not exist'}), 404
  
  pdf_data = io.BytesIO(policy.file_data)

  response = send_file(pdf_data, as_attachment=True, attachment_filename=policy.title + '.pdf',
                       mimetype='application/pdf')
  
  return response


@eadminBP.route('/update_policy', methods=['POST'])
def update_policy():
  policy_id = request.form.get('policyId')
  if not policy_id:
    return jsonify({'error': 'Lack of policyId'}), 400
  
  policy = Policy.query.get(policy_id)
  if not policy:
    return jsonify({'error': 'file does not exist'}), 404
  
  if 'file' not in request.files:
    return jsonify({'error': 'No new documents were provided'}), 400
  
  file = request.files['file']
  if file.filename == '' or not file.filename.endswith('.pdf'):
    return jsonify({'error': 'Please upload the PDF file'}), 400
  
  policy.file_data = file.read()
  db.session.commit()
  
  return jsonify({'message': f'{policy.title} has been updated successfully.'}), 200


@eadminBP.route('/get-registration-applications', methods=['POST'])
def show_registration_applications():
  try:
    applications = RegistrationApplication.query.filter_by(status=1).all()
    result = []
    
    for app in applications:

      if app.proofDocuments:
        file_url = url_for('eadmin.download_proof', email=app.oconvenerEmail, _external=True)
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


@eadminBP.route('/download-proof/<email>', methods=['GET'])
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


@eadminBP.route('/approve-registration', methods=['POST'])
def approve_registration():
  try:
    data = request.get_json()
    app_id = data.get("applicationId")
    
    application = RegistrationApplication.query.filter_by(applicationId=app_id).first()
    
    if not application:
      return jsonify({"message": f"Application with ID {app_id} not found"}), 404
    
    if application.status != 1:
      return jsonify({"message": "Only applications with status 1 (pending) can be approved"}), 400
    
    application.status = 2
    
    try:
      db.session.commit()
    except Exception as e:
      import traceback
      traceback.print_exc()
      db.session.rollback()
    
    return jsonify({"message": f"Application {app_id} approved successfully"}), 200
  
  except Exception as e:
    return jsonify({"message": "Server error", "error": str(e)}), 500


@eadminBP.route('/reject-registration', methods=['POST'])
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


def parse_interface_file(filename):

  base_url = None
  auth_path = None
  project_root = os.path.dirname(current_app.root_path)
  filename = os.path.join(current_app.root_path, 'config', 'BankInterfaceInfo.txt')
  


  if not os.path.exists(filename):
    raise FileNotFoundError(f"The interface information file does not exist: {filename}")
  try:
    with open(filename, 'r') as file:
      content = file.read()
    
    urn_match = re.search(r'urn:\s*(http://[^\s]+)', content)
    if urn_match:
      base_url = urn_match.group(1)
    
    auth_path_match = re.search(r'path:/hw/bank/authenticate', content)
    if auth_path_match:
      auth_path = "/hw/bank/authenticate"
    
    if not all([base_url, auth_path]):
      raise ValueError("The complete interface information cannot be extracted from the file")
    
    return base_url, auth_path
  
  except Exception as e:
    raise Exception(f"The interface information file reading failed: {str(e)}")


def authenticate_account(base_url, auth_path, account):
  if not base_url or not auth_path:
    raise ValueError("The interface information was not initialized correctly")
  account_data = account.to_dict()
  url = base_url + auth_path
  r = requests.post(url, json=account_data, timeout=5)
  r.raise_for_status()
  auth_result = r.json()
  return r.json()


def is_duplicate_record(account, bank):
  existing_record = db.session.query(BankAccount).filter(
    BankAccount.account == account,
    BankAccount.bank == bank,
    BankAccount.status != 0
  ).first()
  return existing_record is not None


@eadminBP.route('/get_e_dba_bank_account', methods=['GET'])
def get_e_dba_bank_account():
  try:
    account = db.session.query(BankAccount).filter_by(organizationName="E-DBA").first()
    if not account:
      return jsonify({}), 200
    
    return jsonify({
      "account_name": account.name,
      "account_number": account.account,
      "bank": account.bank,
      "password": account.get_password()
    }), 200
  
  except Exception as e:
    db.session.rollback()
    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500


@eadminBP.route('/set_e_dba_bank_account', methods=['POST'])
def set_e_dba_bank_account():
  try:
    base_url, auth_path = parse_interface_file("BankInterfaceInfo.txt")
  except Exception as e:
    return jsonify({"error": "The interface information file cannot be read", "details": str(e)}), 500
  
  try:
    name = request.form.get('name')
    account = request.form.get('account')
    bank = request.form.get('bank')
    password = request.form.get('password')
    
    if not all([name, account, bank, password]):
      return jsonify({"error": "required parameter missing"}), 400
    
    existing = db.session.query(BankAccount).filter_by(organizationName="E-DBA").first()
    
    if existing:
      existing.name = name
      existing.account = account
      existing.bank = bank
      existing.set_password(password)
      auth_result = authenticate_account(base_url, auth_path, existing)

      
      if auth_result.get("status") != "success":
        return jsonify({
          "error": "Account authentication failed.",
          "details": auth_result.get("reason", "unknown error")
        }), 403
      
      db.session.commit()

      return jsonify({
        "message": "The configuration update was successful.",
        "config_id": existing.id
      }), 200
    else:
      new_config = BankAccount(
        name=name,
        account=account,
        bank=bank,
        password=password,
        organizationName="E-DBA"
      )
      
      auth_result = authenticate_account(base_url, auth_path, new_config)
      
      if auth_result.get("status") != "success":
        return jsonify({
          "error": "Account authentication failed.",
          "details": auth_result.get("reason", "unknown error")
        }), 403
      
      db.session.add(new_config)
      db.session.commit()
      return jsonify({
        "message": "The configuration was saved successfully.",
        "config_id": new_config.id
      }), 201
  except Exception as e:
    db.session.rollback()
    return jsonify({
      "error": "Internal error of the server",
      "details": str(e)
    }), 500
