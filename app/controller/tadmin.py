from app.models.question import Question
from app.models.datauser import DataUser
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
import traceback
from app.models import EAdmin, SeniorEAdmin
from app.models.base import db

from app.models.tadmin import TAdmin
from app.models.oconvener import OConvener

tadminBP = Blueprint('tadmin', __name__)


@tadminBP.route('/get-question', methods=['POST'])
def get_Question():
  try:
    if not request.is_json:
      return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    page = data.get('page', 1)
    per_page = data.get('perPage', 20)

    query = Question.query.order_by(Question.questionId.asc())
    
    if 'userEmail' in data:
      query = query.filter(Question.userEmail == data['userEmail'])
    
    if 'answered' in data:
      if data['answered']:
        query = query.filter(Question.answer.isnot(None))
      else:
        query = query.filter(Question.answer.is_(None))
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    result = {
      "questions": [{
        "questionId": item.questionId,
        "question": item.question,
        "userEmail": item.userEmail,
        "answer": item.answer,
      } for item in pagination.items],
      "pagination": {
        "currentPage": pagination.page,
        "totalPages": pagination.pages,
        "totalItems": pagination.total
      }
    }
    
    return jsonify(result), 200
  
  except SQLAlchemyError as e:
    current_app.logger.error(f"Database query failed: {str(e)}")
    return jsonify({"error": "Database operation failed."}), 500
  except Exception as e:
    current_app.logger.error(f"system exception: {str(e)}")
    return jsonify({"error": "Internal error of the server"}), 500


@tadminBP.route('/update-answer', methods=['POST'])
def update_answer():
  try:
    if not request.is_json:
      return jsonify({"error": "The request must be in JSON format"}), 400
    
    data = request.get_json()
    question_id = data.get("questionId")
    new_answer = data.get("answer", "").strip()
    
    if not question_id or new_answer == "":
      return jsonify({"error": "The questionId is missing or the answer content is empty"}), 400
    
    question = db.session.query(Question).filter_by(questionId=question_id).first()
    if not question:
      return jsonify({"error": f"The question with the ID of {question_id} does not exist"}), 404
    
    question.answer = new_answer
    db.session.commit()
    
    return jsonify({"message": "The answer has been updated."}), 200
  
  except Exception as e:
    import traceback
    traceback.print_exc()
    db.session.rollback()
    return jsonify({"error": "Internal error of the server", "detail": str(e)}), 500


@tadminBP.route('/submit-question', methods=['POST'])
def submit_question():
  try:
    if not request.is_json:
      return jsonify({"error": "The request must be in JSON format"}), 400
    
    data = request.get_json()
    question_text = data.get("question", "").strip()
    user_id = data.get("userId")
    
    if question_text == "" or not user_id:
      return jsonify({"error": "The problem content or userId is missing"}), 400
    
    user = db.session.query(DataUser).filter_by(userId=user_id).first()
    if not user:
      return jsonify({"error": f"The user with the ID of {user_id} does not exist"}), 404
    
    new_question = Question(
      question=question_text,
      answer=None,
      userEmail=user.email
    )
    
    db.session.add(new_question)
    db.session.commit()
    
    return jsonify({"message": "The question has been submitted.", "questionId": new_question.questionId}), 200
  
  except Exception as e:
    import traceback
    traceback.print_exc()
    db.session.rollback()
    return jsonify({"error": "Internal error of the server", "detail": str(e)}), 500


@tadminBP.route('/get-question-belongto-user', methods=['POST'])
def get_Question_Belongto_User():
  try:
    if not request.is_json:
      return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    user_id = data.get("userId")
    
    page = data.get('page', 1)
    per_page = data.get('perPage', 20)
    
    datauser = DataUser.query.filter_by(userId=user_id).first()
    if not datauser:
      return jsonify({"error": "No data user"}), 500
    email = datauser.email
    
    query = Question.query.filter_by(userEmail=email).order_by(Question.questionId.asc())
    
    if 'answered' in data:
      if data['answered']:
        query = query.filter(Question.answer.isnot(None))
      else:
        query = query.filter(Question.answer.is_(None))
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    result = {
      "questions": [{
        "questionId": item.questionId,
        "question": item.question,
        "userEmail": item.userEmail,
        "answer": item.answer,
      } for item in pagination.items],
      "pagination": {
        "currentPage": pagination.page,
        "totalPages": pagination.pages,
        "totalItems": pagination.total
      }
    }
    
    return jsonify(result), 200
  
  except SQLAlchemyError as e:
    current_app.logger.error(f"Database query failed: {str(e)}")
    return jsonify({"error": "Database operation failed."}), 500
  except Exception as e:
    current_app.logger.error(f"system exception: {str(e)}")
    return jsonify({"error": "Internal error of the server"}), 500


@tadminBP.route('/set-admin', methods=['POST'])
def set_admin():
  try:
    data = request.get_json()
    
    roleType = data.get("roleType")
    userName = data.get("userName")
    userEmail = data.get("userEmail")
    tadmin_userId = data.get("tadminId")
    tadminId = TAdmin.query.filter_by(userId=tadmin_userId).first().tadminId
    userId = get_max_user_id()
    
    if roleType not in ['EAdmin', 'SeniorEAdmin']:
      return jsonify({"error": "Invalid role type"}), 400
    
    if check_email_exists(userEmail, roleType):
      return jsonify({"error": "Email already registered"}), 409
    
    if roleType == 'EAdmin':
      new_admin = EAdmin(
        userName=userName,
        email=userEmail,
        accessLevel=roleType,
        tadminId=tadminId,
        authcode=None,
        userId=userId
      )
    else:
      new_admin = SeniorEAdmin(
        userName=userName,
        email=userEmail,
        accessLevel=roleType,
        tadminId=tadminId,
        authcode=None,
        userId=userId
      )
    
    db.session.add(new_admin)
    db.session.commit()
    
    return jsonify({
      "message": f"{data['roleType']} created successfully",
    }), 201
  
  except SQLAlchemyError as e:
    db.session.rollback()
    traceback.print_exc()
    return jsonify({"error": "Database error"}), 500
  except Exception as e:
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


@tadminBP.route('/update-admin', methods=['POST'])
def update_admin():
  try:
    data = request.get_json()
    
    roleType = data.get("roleType")
    userName = data.get("userName")
    userEmail = data.get("userEmail")
    eadminId = data.get("userId")
    
    # 验证角色类型
    if roleType not in ['EAdmin', 'SeniorEAdmin']:
      return jsonify({"error": "Invalid role type"}), 400
    
    if check_email_exists(userEmail, roleType, exclude_user_id=eadminId):
      return jsonify({"error": "Email already used by another user"}), 409
    
    if roleType == 'EAdmin':
      admin = EAdmin.query.filter_by(eadminId=eadminId).first()
    else:
      admin = SeniorEAdmin.query.filter_by(eadminId=eadminId).first()
    
    if not admin:
      return jsonify({"error": "Admin not found"}), 404
    
    admin.userName = userName
    admin.email = userEmail
    
    db.session.commit()
    
    return jsonify({"message": "Admin updated successfully"}), 200
  
  except SQLAlchemyError as e:
    db.session.rollback()
    traceback.print_exc()
    return jsonify({"error": "Database error"}), 500
  except Exception as e:
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500


def check_email_exists(email, roleType, exclude_user_id=None):
  if roleType == 'EAdmin':
    query = EAdmin.query.filter(EAdmin.email == email)
    if exclude_user_id:
      query = query.filter(EAdmin.eadminId != exclude_user_id)
  else:
    query = SeniorEAdmin.query.filter(SeniorEAdmin.email == email)
    if exclude_user_id:
      query = query.filter(SeniorEAdmin.eadminId != exclude_user_id)
  
  return query.first() is not None


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


@tadminBP.route('/get-admin', methods=['POST'])
def get_admin():
  try:
    eadmin_query = EAdmin.query
    senior_query = SeniorEAdmin.query
    
    eadmins = eadmin_query.all()
    senior_eadmins = senior_query.all()
    
    result = []
    
    for eadmin in eadmins:
      result.append({
        "id": eadmin.eadminId,
        "userName": eadmin.userName,
        "email": eadmin.email,
        "roleType": "EAdmin"
      })
    
    for seadmin in senior_eadmins:
      result.append({
        "id": seadmin.eadminId,
        "userName": seadmin.userName,
        "email": seadmin.email,
        "roleType": "SeniorEAdmin"
      })
    
    return jsonify({"admins": result}), 200
  
  except SQLAlchemyError as e:
    current_app.logger.error(f"Database query failed: {str(e)}")
    return jsonify({"error": "Database operation failed."}), 500
  except Exception as e:
    current_app.logger.error(f"system exception: {str(e)}")
    return jsonify({"error": "Internal error of the server"}), 500
