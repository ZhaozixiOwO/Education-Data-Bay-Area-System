from flask import Blueprint, request, jsonify, current_app
from app.models.bankaccount import BankAccount
from app.models.datauser import DataUser
from app.models.oconvener import OConvener
from app.models.pay import Pay
from app.models.base import db
import requests
import re
import os

payBP = Blueprint('pay', __name__)


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
    
    auth_path_match = re.search(r'path:/hw/bank/transfer', content)
    if auth_path_match:
      auth_path = "/hw/bank/transfer"
    
    if not all([base_url, auth_path]):
      raise ValueError("The complete interface information cannot be extracted from the file")
    
    return base_url, auth_path
  
  except Exception as e:
    raise Exception(f"The interface information file reading failed: {str(e)}")


@payBP.route('/transfer_funds', methods=['POST'])
def transfer_funds():
  edbabank = BankAccount.query.filter_by(organizationName="E-DBA").first()
  if not edbabank:
    raise ValueError("The edba bank account has not been set up")
  to_bank = edbabank.bank
  to_name = edbabank.name
  to_account = edbabank.account

  userId = request.args.get('userId')
  price = request.args.get('price')
  
  if not userId:
    raise ValueError("The userid was not obtained")

  datauser = DataUser.query.filter_by(userId=userId).first()
  if not datauser:
    oconvener = OConvener.query.filter_by(userId=userId).first()
  else:
    oconvener = OConvener.query.filter_by(convenerId=datauser.convenerId).first()

  bank_account = BankAccount.query.filter_by(organizationName=oconvener.organizationName).first()
  
  if not bank_account:
    raise ValueError("The bank account information was not obtained")
  from_bank = bank_account.bank
  from_name = bank_account.name
  from_account = bank_account.account
  password = bank_account.get_password()

  payload = {
    "from_bank": from_bank,
    "from_name": from_name,
    "from_account": from_account,
    "password": password,
    "to_bank": to_bank,
    "to_name": to_name,
    "to_account": to_account,
    "amount": price
  }

  base_url, auth_path = parse_interface_file("BankInterfaceInfo.txt")
  if not base_url or not auth_path:
    raise ValueError("The interface information was not initialized correctly")
  
  url = base_url + auth_path

  try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
      res_json = response.json()
      if res_json.get("status") == "success":
        pay_record = Pay(
          amount=price,
          receiver=to_name,
          sender=bank_account.name
        )
        db.session.add(pay_record)
        db.session.commit()
        return jsonify({'success': True, 'account_info': bank_account.to_dict()}), 200
      else:
        return jsonify({'false': False, 'reason': res_json.get("reason", "Unknown error")}), 400
    else:
      return jsonify({'false': False, 'reason': "The transfer interface returns an error"}), 400
  except Exception as e:
    return jsonify({'false': False, 'reason': str(e)}), 500


@payBP.route('/check_quota', methods=['GET'])
def check_quota():
  user_id = request.args.get('userId')
  price = request.args.get('price')

  if not user_id or price is None:
    return jsonify({"error": "The userId or price parameters are missing"}), 400
  try:
    price = float(price)
  except ValueError:
    return jsonify({"error": "The price format is incorrect"}), 400
  datauser = db.session.query(DataUser).filter_by(userId=user_id).first()
  if not datauser:
    return jsonify({"error": "The user does not exist."}), 404
  
  quota = datauser.quota
  sufficient = quota >= price
  
  return jsonify({
    "sufficient": sufficient,
    "remainingQuota": quota
  })


@payBP.route('/deduct_quota', methods=['POST'])
def deduct_quota():
  user_id = request.args.get('userId')
  price = request.args.get('price')
  if not user_id or price is None:
    return jsonify({"error": "The userId or price parameters are missing"}), 400
  try:
    price = float(price)
  except ValueError:
    return jsonify({"error": "The price format is incorrect"}), 400
  
  datauser = db.session.query(DataUser).filter_by(userId=user_id).first()
  if not datauser:
    return jsonify({"error": "The user does not exist."}), 404
  quota = datauser.quota
  balance = quota - price
  datauser.quota = balance
  db.session.commit()
  return jsonify({
    "message": "Deduction successful",
    "remainingQuota": datauser.quota
  })
