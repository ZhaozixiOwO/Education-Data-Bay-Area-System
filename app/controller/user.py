import logging
import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.models.base import db
from app.models.datauser import DataUser
from app.models.eadmin import EAdmin
from app.models.oconvener import OConvener
from app.models.senioreadmin import SeniorEAdmin
from app.models.tadmin import TAdmin
from flask import jsonify, request, Blueprint


userBP = Blueprint('user', __name__)



logging.basicConfig(level=logging.INFO)
userBP.logger = logging.getLogger('E-DBA Auth Service')


os.environ['SMTP_USER'] = 'j1051620740@gmail.com'
os.environ['SMTP_PASSWORD'] = 'aydl grvr jjlk ckag'


SMTP_CONFIG = {
  "server": "smtp.gmail.com",
  "port": 587,
  "sender": os.getenv('SMTP_USER'),
  "password": os.getenv('SMTP_PASSWORD'),
  "timeout": 30
}


def send_verification_email(receiver_email: str, vcode: str) -> bool:

  msg = MIMEMultipart()
  msg["From"] = SMTP_CONFIG['sender']
  msg["To"] = receiver_email
  msg["Subject"] = "E-DBA Verification Code"
  
  email_body = f"Your verify code is {vcode}."
  
  msg.attach(MIMEText(email_body, "html", "utf-8"))
  
  with smtplib.SMTP(
    host=SMTP_CONFIG['server'],
    port=SMTP_CONFIG['port'],
    timeout=SMTP_CONFIG['timeout']
  ) as server:
    server.starttls()
    server.login(SMTP_CONFIG['sender'], SMTP_CONFIG['password'])
    server.sendmail(SMTP_CONFIG['sender'], receiver_email, msg.as_string())
    userBP.logger.info(f"The email was successfully sent to: {receiver_email}")
    return True


@userBP.route('/send-verify-code', methods=['POST'])
def handle_verification():
  try:
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    identity = data.get('identity', '').upper()
    
    if not all([email, identity]):
      return jsonify({"code": "INVALID_REQUEST", "message": "The email address and identity cannot be empty"}), 400
    

    if identity == 'O':
      user = db.session.query(OConvener).filter_by(email=email).first()
    elif identity == 'E':
      user = db.session.query(EAdmin).filter_by(email=email).first()
    elif identity == 'S':
      user = db.session.query(SeniorEAdmin).filter_by(email=email).first()
    elif identity == 'T':
      user = db.session.query(TAdmin).filter_by(email=email).first()
    elif identity == 'D':
      user = db.session.query(DataUser).filter_by(email=email).first()
    else:
      return jsonify({
        "code": "INVALID_IDENTITY",
        "message": "Invalid identity identifier"
      }), 400
    
    if not user:
      return jsonify({
        "code": "USER_NOT_FOUND",
        "message": "The user does not exist"
      }), 404
    
    vcode = ''.join(random.choices('0123456789', k=6))
    expiration = datetime.now() + timedelta(minutes=5)
    
    print(f"Verify code is {vcode}.")
    
    user.authcode = vcode
    db.session.commit()
    
    send_verification_email(email, vcode)
    
    return jsonify({
      "code": "SUCCESS",
      "message": "The verification code has been sent to the registered email",
      "data": {
        "expires_in": 300,
        "masked_email": f"***{email[-4:]}"
      }
    }), 200
  
  except Exception as e:
    db.session.rollback()
    userBP.logger.error(f"system exception: {str(e)}", exc_info=True)
    return jsonify({
      "code": "SYSTEM_ERROR",
      "message": "The system service is temporarily unavailable"
    }), 500


@userBP.route('/login', methods=['POST'])
def login():
  try:
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    input_code = data.get('code', '').strip()
    identity = data.get('identity', '').upper()
    
    if not all([email, input_code, identity]):
      return jsonify({
        "code": "INVALID_REQUEST",
        "message": "The email address, verification code and identity cannot be empty"
      }), 400
    
    user = None
    user_identity = None
    user_status = None
    
    if identity == 'T':
      user = db.session.query(TAdmin).filter_by(email=email).first()
    elif identity == 'E':
      user = db.session.query(EAdmin).filter_by(email=email).first()
    elif identity == 'S':
      user = db.session.query(SeniorEAdmin).filter_by(email=email).first()
    elif identity == 'O':
      user = db.session.query(OConvener).filter_by(email=email).first()
      user_status = user.status
    elif identity == 'D':
      user = db.session.query(DataUser).filter_by(email=email).first()
      if user:
        user_identity = user.identity
    else:
      return jsonify({
        "code": "INVALID_IDENTITY",
        "message": "Identity invalid. Please select the correct identity"
      }), 400
    
    user_status = user.status
    
    if not user:
      return jsonify({
        "code": "USER_NOT_FOUND",
        "message": "The user does not exist. Please contact the administrator"
      }), 404
    
    if not user.authcode:
      return jsonify({
        "code": "CODE_EXPIRED",
        "message": "The verification code has not been sent or has expired. Please obtain it again"
      }), 404
    
    if input_code != user.authcode:
      return jsonify({
        "code": "INVALID_CODE",
        "message": "Verification code error"
      }), 401
    
    if identity == 'O':
      if user.accessLevel != 'OConvener':
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "The O-Convener permission does not match"
        }), 403
      if user_status != 1:
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "This user is unable to log in"
        })
    elif identity == 'E':
      if user.accessLevel != 'EAdmin':
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "The E-Admin permission does not match"
        }), 403
      if user_status != 1:
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "This user is unable to log in"
        })
    elif identity == 'S':
      if user.accessLevel != 'SeniorEAdmin':
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "The permissions of Senior E-Admin do not match"
        }), 403
      if user_status != 1:
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "This user is unable to log in"
        })
    elif identity == 'T':
      if user.accessLevel != 'TAdmin':
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "The T-Admin permission does not match"
        }), 403
      if user_status != 1:
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "This user is unable to log in"
        })
    elif identity == 'D':
      if user.accessLevel != 'Data User':
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "The permissions of Data User do not match"
        }), 403
      # Data User additional checksum sub-identity
      if user_identity not in ['1', '2', '3']:
        return jsonify({
          "code": "INVALID_SUBTYPE",
          "message": "Data User Data user subtype exception"
        }), 403
      if user_status != 2:
        return jsonify({
          "code": "ACCESS_DENIED",
          "message": "This user is unable to log in"
        })
    
    userId = user.userId
    
    # 确定跳转路径
    if identity == 'D':
      if user_identity == "2":
        redirect_url = '/frontend/private-data-consumer'
      elif user_identity == "3":
        redirect_url = '/frontend/private-data-provider'
      elif user_identity == "1":
        redirect_url = '/frontend/public-data-consumer'
    elif identity == 'T':
      redirect_url = '/frontend/tadmin'
    elif identity == 'E':
      redirect_url = '/frontend/eadmin'
    elif identity == 'S':
      redirect_url = '/frontend/senior-eadmin'
    elif identity == 'O':
      redirect_url = '/frontend/oconvener'
    else:
      redirect_url = 'frontend/login'
    
    return jsonify({
      "code": "LOGIN_SUCCESS",
      "message": "successful authentication",
      "data": {
        "redirect": redirect_url,
        "user_info": {
          "email": email,
          "identity": user.accessLevel,
          "user_id": userId,
          "login_time": datetime.now().isoformat()
        }
      }
    }), 200
  
  except Exception as e:
    userBP.logger.error(f"Login anomaly:{str(e)}", exc_info=True)
    return jsonify({
      "code": "SYSTEM_ERROR",
      "message": "The login service is temporarily unavailable"
    }), 500


@userBP.route('/logout', methods=['POST'])
def logout():
  user_id = request.args.get('userId')
  if not user_id:
    return jsonify({"error": "The userId parameter is missing"
                             ""}), 400
  
  try:
    user = db.session.query(DataUser).filter_by(userId=user_id).first()
    if user:
      user.authcode = None
    else:
      user = db.session.query(TAdmin).filter_by(userId=user_id).first()
      if user:
        user.authcode = None
      else:
        user = db.session.query(EAdmin).filter_by(userId=user_id).first()
        if user:
          user.authcode = None
        else:
          user = db.session.query(OConvener).filter_by(userId=user_id).first()
          if user:
            user.authcode = None
          else:
            user = db.session.query(SeniorEAdmin).filter_by(userId=user_id).first()
            if user:
              user.authcode = None
            else:
              return jsonify({"error": "The user whose corresponding identity was not found"}), 403
    db.session.commit()
    return jsonify({"message": "The user has successfully logged out", "userId": user_id}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500