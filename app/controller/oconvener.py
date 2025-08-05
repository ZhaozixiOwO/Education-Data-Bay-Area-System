import logging
import os
import random
import re
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import requests
from app.models.bankaccount import BankAccount
from app.models.base import db
from app.models.datauser import DataUser
from app.models.eadmin import EAdmin
from app.models.oconvener import OConvener
from app.models.registrationapplication import RegistrationApplication
from app.models.tadmin import TAdmin
from app.models.workspace import Workspace
from flask import Blueprint, request, jsonify
from flask import current_app, url_for
from sqlalchemy import func

oconvenerBP = Blueprint('oconvener', __name__)

logging.basicConfig(level=logging.INFO)
oconvenerBP.logger = logging.getLogger('E-DBA Auth Service')

os.environ['SMTP_USER'] = 'j1051620740@gmail.com'
os.environ['SMTP_PASSWORD'] = 'aydl grvr jjlk ckag'

SMTP_CONFIG = {
  "server": "smtp.gmail.com",
  "port": 587,
  "sender": os.getenv('SMTP_USER'),
  "password": os.getenv('SMTP_PASSWORD'),
  "timeout": 10
}


verification_codes = {}
DATABASE_CONFIG = {
}


def send_verification_email(receiver_email: str, vcode: str) -> bool:

  msg = MIMEMultipart()
  msg["From"] = SMTP_CONFIG['sender']
  msg["To"] = receiver_email
  msg["Subject"] = "E-DBA Verification Code"
  
  email_body = f"Your verify code is {vcode}."
  
  msg.attach(MIMEText(email_body, "html", "utf-8"))
  
  for attempt in range(3):
    try:
      with smtplib.SMTP(
        host=SMTP_CONFIG['server'],
        port=SMTP_CONFIG['port'],
        timeout=SMTP_CONFIG['timeout']
      ) as server:
        server.starttls()
        server.login(SMTP_CONFIG['sender'], SMTP_CONFIG['password'])
        server.sendmail(SMTP_CONFIG['sender'], receiver_email, msg.as_string())
        oconvenerBP.logger.info(f"The email was successfully sent to: {receiver_email}")
        return True
    except smtplib.SMTPAuthenticationError:
      oconvenerBP.logger.error("SMTP authentication failed. Please check the email password")
      return False
    except Exception as e:
      oconvenerBP.logger.warning(f"Email sending failed ({attempt + 1}/3): {str(e)}")
      continue
  return False


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
    raise Exception(f"Interface information file reading failed: {str(e)}")


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


@oconvenerBP.route('/get_bank_account', methods=['GET'])
def get_bank_account():
  try:
    user_id = request.args.get('userId')
    
    if not user_id:
      return jsonify({"error": "The userId parameter is missing"}), 400
    
    oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
    if not oconvener:
      return jsonify({"error": "OConvener was not found"}), 404
    
    org_name = oconvener.organizationName
    account = db.session.query(BankAccount).filter_by(organizationName=org_name).first()
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


@oconvenerBP.route('/set_bank_account', methods=['POST'])
def set_bank_account():
  try:
    base_url, auth_path = parse_interface_file("BankInterfaceInfo.txt")
  except Exception as e:
    return jsonify({"error": "The interface information file cannot be read", "details": str(e)}), 500
  
  try:
    user_id = request.args.get('userId')
    if not user_id:
      return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
    
    oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
    if not oconvener:
      return jsonify({"error": "The corresponding OConvener couldn't be found"}), 405
    
    oName = oconvener.organizationName
  
  except Exception as e:
    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500
  
  try:
    name = request.form.get('name')
    account = request.form.get('account')
    bank = request.form.get('bank')
    password = request.form.get('password')
    if not all([name, account, bank, password]):
      return jsonify({"error": "required parameter missing"}), 400
    
    existing = db.session.query(BankAccount).filter_by(organizationName=oName).first()
    
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
        organizationName=oName
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


@oconvenerBP.route('/create_service', methods=['POST'])
def create_service():
  user_id = request.args.get('userId')
  if not user_id:
    return jsonify({"error": "The user is not logged in."}), 401
  
  oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
  if not oconvener:
    return jsonify({"error": "Invalid user"}), 404
  
  data = request.get_json()
  service_type = data.get('serviceType')
  if not service_type:
    return jsonify({"error": "Lack of service types"}), 400
  existing_service = db.session.query(Workspace).filter_by(
    convenerId=oconvener.convenerId,
    service=service_type
  ).first()
  
  if existing_service:
    return jsonify({"error": "This service already exists and cannot be added again"}), 409
  
  if service_type == "course":
    new_service = Workspace(
      convenerId=oconvener.convenerId,
      service=service_type,
      price=0.0,
    )
    new_service.status = 2
  else:
    new_service = Workspace(
      convenerId=oconvener.convenerId,
      service=service_type,
      price=0.0,
    )
  db.session.add(new_service)
  db.session.commit()
  
  return jsonify({"message": "The service was successfully created."}), 201


@oconvenerBP.route('/get_workspace_service', methods=['GET'])
def get_workspace_service():
  try:
    user_id = request.args.get('userId')
    
    if not user_id:
      return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
    
    oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
    if not oconvener:
      return jsonify({"error": "The corresponding OConvener couldn't be found"}), 404
    
    convener_id = oconvener.convenerId

    workspace = db.session.query(Workspace).filter_by(convenerId=convener_id).all()

    if not workspace:
      return jsonify({"error": "The corresponding Workspace was not found"}), 404
    result = [{
      "convenerId": convener_id,
      "serviceId": w.id,
      "portContent": w.service,
      "status": w.status,
      "price": w.price
    } for w in workspace]
    print(result)
    return jsonify(result), 200
  
  except Exception as e:
    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500


@oconvenerBP.route('/update_workspace_service', methods=['POST'])
def update_workspace_service():
  try:
    data = request.get_json()
    updates = data.get('updates', [])
    for item in updates:
      service = item['serviceId']
      portContent = item['portContent']
      enabled = item['enabled']
      price = item['price']

      workspace = db.session.query(Workspace).filter_by(id=service).first()
      if workspace:
        # if portContent in ["Course", "Thesis"]:
        #   workspace.price = 0
        # else:
        #   workspace.price = price
        workspace.price = price
        workspace.status = enabled
        print(workspace.price)
        print(workspace.status)
    db.session.commit()
    return jsonify({"message": "update successfully"}), 200
  
  except Exception as e:
    db.session.rollback()
    return jsonify({"error": "update failed", "details": str(e)}), 50


def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx', 'pdf'}


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


@oconvenerBP.route('/members/import', methods=['POST'])
def import_members():
  try:
    user_id = request.args.get('userId')
    if not user_id:
      return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
    
    oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
    if not oconvener:
      return jsonify({"error": "The corresponding OConvener couldn't be found"}), 405
    convenerId = oconvener.convenerId
  except Exception as e:
    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500
  
  if 'file' not in request.files:
    return jsonify({'error': 'Missing documents'}), 400
  
  file = request.files['file']
  if file.filename == '' or not allowed_file(file.filename):
    return jsonify({'error': 'Invalid file'}), 400
  
  
  try:
    df = pd.read_excel(file)
  except Exception as e:
    return jsonify({'error': 'The Excel file cannot be read', 'details': str(e)}), 500
  
  required = ['name', 'email', 'access right', 'Quota for thesis download']
  if not all(col in df.columns for col in required):
    return jsonify({'error': 'Excel is lacking necessary columns'}), 400
  
  imported = 0
  try:
    for _, row in df.iterrows():
      if pd.isna(row['name']) or pd.isna(row['email']):
        continue
      
      try:
        quota_raw = str(row['Quota for thesis download']).replace('RMB', '').strip()
        quota = int(re.sub(r'[^0-9]', '', quota_raw))
      except:
        quota = 0
      
      userName = row['name']
      email = row['email']
      accessLevel = str(row['access right'])
      
      exists = db.session.query(DataUser).filter_by(
        email=email, userName=userName, convenerId=convenerId
      ).first()
      if exists:
        continue
      
      x = get_max_user_id() + 1
      
      user = DataUser(
        userId=x,
        userName=userName,
        email=email,
        convenerId=convenerId,
        accessLevel="Data User",
        identity=accessLevel,
        quota=quota,
        authcode=None
      )
      db.session.add(user)
      imported += 1
    
    db.session.commit()

  except Exception as e:
    db.session.rollback()
    return jsonify({'error': 'Import failed', 'details': str(e)}), 500

  
  return jsonify({'message': 'Import successful', 'count': imported}), 200


@oconvenerBP.route('/members', methods=['GET'])
def get_members():
  user_id = request.args.get('userId')
  
  if not user_id:
    return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
  

  oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
  if not oconvener:
    return jsonify({"error": "The corresponding OConvener couldn't be found"}), 404
  
  convener_id = oconvener.convenerId
  dataUser = db.session.query(DataUser).filter_by(convenerId=convener_id).all()
  return jsonify([{
    'userId': m.dataUserId,
    'userName': m.userName,
    'email': m.email,
    'identity': m.identity,
    'quota': m.quota,
    'status': m.status,
  } for m in dataUser]), 200


@oconvenerBP.route('/members/add', methods=['POST'])
def add_member():
  try:
    user_id = request.args.get('userId')
    if not user_id:
      return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
    
    oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
    if not oconvener:
      return jsonify({"error": "The corresponding OConvener couldn't be found"}), 405
    
    convenerId = oconvener.convenerId
  
  except Exception as e:
    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500
  
  try:
    
    data = request.get_json()
    
    userName = data.get('userName')
    email = data.get('email')
    accessLevel = data.get('accessLevel')
    thesisDownloadQuota = data.get('thesisDownloadQuota', 0)
    
    if not all([userName, email, accessLevel]):
      return jsonify({"error": "required parameter missing"}), 400
    
    exists = db.session.query(DataUser).filter_by(
      email=email, userName=userName, convenerId=convenerId
    ).first()
    if exists:
      return jsonify({"error": "This member already exists. Please do not add it again"}), 409
    
    x = get_max_user_id() + 1
    user = DataUser(
      userId=x,
      userName=userName,
      email=email,
      convenerId=convenerId,
      accessLevel="Data User",
      identity=accessLevel,
      quota=thesisDownloadQuota,
      authcode=None
    )
    
    db.session.add(user)
    db.session.flush()
    
    db.session.commit()
    
    return jsonify({
      "message": "successfully added",
      "userId": user.userId,
    }), 200
  
  except Exception as e:
    db.session.rollback()
    return jsonify({
      "error": "Internal error of the server",
      "details": str(e)
    }), 500


@oconvenerBP.route('/members/edit', methods=['POST'])
def edit_member():
  try:
    data = request.get_json()
    datauserId = data.get('datauserId')
    userName = data.get('userName')
    email = data.get('email')
    identity = data.get('accessLevel')
    quota = data.get('thesisDownloadQuota', 0)
    status = data.get('status')
    
    datauser = db.session.query(DataUser).filter_by(dataUserId=datauserId).first()
    
    if datauser:
      datauser.userName = userName
      datauser.email = email
      datauser.identity = identity
      datauser.quota = quota
      datauser.status = status
    else:
      return jsonify({"message": "error"}), 200
    db.session.commit()
    return jsonify({"message": "update successfully"}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({"error": "Update failed", "details": str(e)}), 500


@oconvenerBP.route('/members/pay', methods=['POST'])
def pay_one_member():
  try:
    datauserId = request.args.get('datauserId')
    user_id = request.args.get('userId')
    print(datauserId)
    if not user_id:
      return jsonify({"error": " The user is not logged in or the session is invalid"}), 407

    eadmin = db.session.query(EAdmin).filter_by(status=1).first()
    if not eadmin or not eadmin.membershipFee:
      return jsonify({"error": "No effective membership fee rules have been found"}), 406

    fee_map = eadmin.membershipFee

    member = db.session.query(DataUser).filter_by(dataUserId=datauserId).first()

    if not member:
      return jsonify({"error": "Member was not found"}), 409
    status = member.status
    level = member.identity
    if not member:
      return jsonify({"error": "The member was not found"}), 404
    if status == 2:
      return jsonify({"error": "The member has paid the fee"}), 405
    if status == 0:
      return jsonify({"error": "This member is not enabled"}), 403
    labels = ['Public data access', 'Private data consumption', 'Private data provision']
    level = int(level)
    if level not in [1, 2, 3]:
      return jsonify({"error": f"Unknown access level: {level}"}), 400
    fee_key = f"Access right level {level}({['Public data access', 'Private data consumption', 'Private data provision'][level - 1]})"
    fee_key = fee_key + ":"
    fee = fee_map.get(fee_key, 0)
    if fee == 0:
      return jsonify({"error": "The permission level is unknown and the cost cannot be calculated"}), 401

    transfer_url = url_for('pay.transfer_funds', _external=True)
    response = requests.post(
      transfer_url,
      params={'userId': user_id, 'price': fee}
    )

    result = response.json()

    if not result.get("success"):
      return jsonify({"error": "payment failure", "reason": result.get("reason")}), 402

    member.status = 2
    db.session.commit()

    return jsonify({
      'message': f'member {member.userName} has successfully paid. The total fee is ¥{fee}.',
      'userId': member.userId,
      'fee': fee
    }), 200

  except Exception as e:
    db.session.rollback()
    return jsonify({'error': 'server error', 'details': str(e)}), 500


@oconvenerBP.route('/members/pay_all', methods=['POST'])
def pay_all_members():
  try:

    user_id = request.args.get('userId')
    if not user_id:
      return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
    
    oconvener = db.session.query(OConvener).filter_by(userId=user_id).first()
    if not oconvener:
      return jsonify({"error": "The corresponding OConvener couldn't be found"}), 405
    
    organization_name = oconvener.organizationName
    unpaid_members = db.session.query(DataUser).filter_by(status=1, convenerId=oconvener.convenerId).all()

    if not unpaid_members:
      return jsonify({"error": "There are no members who have not paid for the time being"}), 400
    eadmin = db.session.query(EAdmin).filter_by(status=1).first()
    if not eadmin or not eadmin.membershipFee:
      return jsonify({"error": "No effective membership fee rules have been found"}), 400
    
    fee_map = eadmin.membershipFee

    total_fee = 0
    to_update = []
    
    for member in unpaid_members:
      identity_int = int(member.identity)
      fee_key = f"Access right level {identity_int}({['Public data access', 'Private data consumption', 'Private data provision'][identity_int - 1]})"
      fee_key = fee_key + ":"
      fee = fee_map.get(fee_key, 0)
      total_fee += fee
      to_update.append(member)
    
    transfer_url = url_for('pay.transfer_funds', _external=True)
    response = requests.post(
      transfer_url,
      params={'userId': user_id, 'price': total_fee}
    )
    result = response.json()
    if not result.get("success"):
      db.session.rollback()
      return jsonify({"error": "Batch payment failed", "reason": result.get("reason")}), 400
    
    for member in to_update:
      member.status = 2
    
    db.session.commit()
    return jsonify({
      'message': f'Batch payment was successful. A total of {len(to_update)} people, with a total fee of ¥{total_fee}.',
      'updated': len(to_update),
      'totalFee': total_fee
    }), 200
  
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': 'server error', 'details': str(e)}), 500


@oconvenerBP.route('/register/send-verify-code', methods=['POST'])
def register_get_verify_code():
  try:
    data = request.get_json()
    email = data.get('email', '').lower().strip()
    org_name = data.get('organizationName', '').strip()
    
    if not all([email, org_name]):
      return jsonify({"code": "INVALID_REQUEST", "message": "The email address and organization name cannot be empty"}), 400
    
    vcode = ''.join(random.choices('0123456789', k=6))
    
    app_entry = RegistrationApplication.query.filter_by(oconvenerEmail=email).first()
    
    if app_entry:
      app_entry.regisCode = vcode
    else:
      app_entry = RegistrationApplication(
        organizationName=org_name,
        oconvenerEmail=email,
        proofDocuments=b'',
        regisCode=vcode,
      )
      app_entry.status = 0
      db.session.add(app_entry)
    
    db.session.commit()
    
    if not send_verification_email(email, vcode):
      app_entry.regisCode = None
      db.session.commit()
      return jsonify({"code": "EMAIL_FAILURE", "message": "e-mail sending failed"}), 503
    print(f"Verify code is {vcode}.")
    return jsonify({
      "code": "SUCCESS",
      "message": "The authcode has been sent",
      "data": {"masked_email": f"***{email[-4:]}"}
    }), 200
  
  except sqlite3.IntegrityError:
    db.session.rollback()
    return jsonify({"code": "DB_ERROR", "message": "Database error"}), 400
  except Exception as e:
    db.session.rollback()
    current_app.logger.error(f"Verification error: {str(e)}")
    return jsonify({"code": "SYSTEM_ERROR", "message": "system exception"}), 500


@oconvenerBP.route('/register', methods=['POST'])
def regist():
  try:
    email = request.form.get('email', '').lower().strip()
    vcode = request.form.get('verificationCode', '').strip()
    org_name = request.form.get('organizationName', '').strip()
    document = request.files.get('document')
    
    if not all([email, vcode, org_name]) or not document:
      return jsonify({"code": "INVALID_REQUEST", "message": "Missing required fields"}), 400
    
    app_entry = RegistrationApplication.query.filter_by(oconvenerEmail=email).first()
    if not app_entry:
      return jsonify({"code": "INVALID_APPLICATION", "message": "The registration application was not found"}), 404
    
    if app_entry.regisCode != vcode:
      return jsonify({"code": "INVALID_CODE", "message": "Authcode error"}), 401
    

    if not allowed_file(document.filename):
      return jsonify({"code": "INVALID_FILE", "message": "Invalid file type"}), 400
    
    pdf_bytes = document.read()
    app_entry.proofDocuments = pdf_bytes
    app_entry.status = 1
    db.session.commit()
    
    return jsonify({
      "code": "REGISTRATION_SUCCESS",
      "message": "registered successfully",
      "data": {
        "organization": org_name
      }
    }), 200
  
  except Exception as e:
    db.session.rollback()
    current_app.logger.error(f"Registration error: {str(e)}")
    return jsonify({"code": "SYSTEM_ERROR", "message": "An anomaly occurred during the registration process"}), 500


@oconvenerBP.route('/register/withdraw-registration', methods=['POST'])
def withdraw_registration():
  try:
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    app_entry = RegistrationApplication.query.filter_by(oconvenerEmail=email).first()
    if not app_entry:
      return jsonify({"code": "NOT_FOUND", "message": "The corresponding application record was not found"}), 404
    
    app_entry.status = 0
    db.session.commit()
    
    return jsonify({
      "code": "WITHDRAW_SUCCESS",
      "message": "Revocation successful"
    }), 200
  
  except Exception as e:
    db.session.rollback()
    current_app.logger.error(f"Withdraw error: {str(e)}")
    return jsonify({"code": "SYSTEM_ERROR", "message": "An exception occurred during the revocation process"}), 500
