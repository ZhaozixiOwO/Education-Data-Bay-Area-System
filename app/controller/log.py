from app.models.base import db
from app.models.datauser import DataUser
from app.models.eadmin import EAdmin
from app.models.log import Log
from app.models.oconvener import OConvener
from app.models.senioreadmin import SeniorEAdmin
from app.models.tadmin import TAdmin
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError

logBP = Blueprint('log', __name__)


@logBP.route('/log-info', methods=['POST'])
def add_log():
  try:
    user_id = request.args.get('userId', type=int)
    identity = request.args.get('identity')
    action = request.args.get('action')
    user_email = None
    
    if not user_id or not identity or not action:
      return jsonify({'error': 'The parameter userId/identity/action is missing'}), 400
    
    if identity == 'TAdmin':
      user = db.session.query(TAdmin).filter_by(userId=user_id).first()
    elif identity == 'EAdmin':
      user = db.session.query(EAdmin).filter_by(userId=user_id).first()
    elif identity == 'SeniorEAdmin':
      user = db.session.query(SeniorEAdmin).filter_by(userId=user_id).first()
    elif identity == 'OConvener':
      user = db.session.query(OConvener).filter_by(userId=user_id).first()
    elif identity == 'Data User':
      user = db.session.query(DataUser).filter_by(userId=user_id).first()
    else:
      return jsonify({'error': 'Identity type invalid'}), 400
    
    if user:
      user_email = user.email
    else:
      return jsonify({'error': 'The corresponding user was not found'}), 404
    
    log = Log(userEmail=user_email, action=action, identity=identity)
    
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'The log recording was successful.'}), 201
  
  except Exception as e:
    db.session.rollback()
    current_app.logger.error(f'Log recording failed.: {e}')
    return jsonify({'error': 'Log recording failed.'}), 500


@logBP.route('/get-log', methods=['POST'])
def get_log():
  try:
    data = request.get_json()
    activity_type = data.get('action')
    email = data.get('userEmail')
    org_name = data.get('organizationName')
    role = data.get('role')
    query = Log.query
    
    if activity_type:
      query = query.filter(Log.action.ilike(f"%{activity_type}%"))
    
    if email:
      query = query.filter(Log.userEmail == email)
    
    if org_name:
      convener = OConvener.query.filter_by(organizationName=org_name).first()
      if convener:
        convener_id = convener.convenerId
        
        user_emails = [datauser.email for datauser in DataUser.query.filter_by(convenerId=convener_id).all()]
        
        query = query.filter(Log.userEmail.in_(user_emails))
      else:
        return jsonify({"logs": []}), 200
    if role:
      query = query.filter(Log.identity == role)
    
    logs = query.order_by(Log.create_time.asc()).all()
    
    result = []
    for log in logs:
      formatted_time = log.create_time.strftime("%Y-%m-%d %H:%M:%S") if log.create_time else None
      result.append({
        "logId": log.logId,
        "timestamp": formatted_time,
        "status": log.status,
        "userEmail": log.userEmail,
        "identity": log.identity,
        "action": log.action,
      })
    
    return jsonify({"logs": result}), 200
  
  except SQLAlchemyError as e:
    current_app.logger.error(f"Database error fetching logs: {str(e)}")
    return jsonify({"error": "Database operation failed"}), 500
  except Exception as e:
    current_app.logger.error(f"Unexpected error: {str(e)}")
    return jsonify({"error": "Server internal error"}), 500


@logBP.route('/get-organization-log', methods=['POST'])
def get_organization_log():
  try:
    if not request.is_json:
      return jsonify({"error": "Content-Type must be application/json"}), 400
    
    try:
      data = request.get_json(force=False, silent=True)
    except Exception as e:
      current_app.logger.error(f"JSON parsing failed.: {str(e)}")
      return jsonify({"error": "Invalid JSON format"}), 400
    

    current_app.logger.debug(f"Original request body: {request.data[:200]}...")
    
    if not data or 'userId' not in data:
      current_app.logger.warning("The request is lacking necessary parameters")
      return jsonify({"error": "Missing required parameter: userId"}), 400
    
    user_id = data['userId']
    
    oconvener = OConvener.query.filter_by(userId=int(user_id)).first()
    if not oconvener:
      return jsonify({"error": "Convener not found"}), 404
    

    user_email = oconvener.email
    if not user_email:
      return jsonify({"error": "Convener email not found"}), 404
    
    page = data.get('page', 1)
    per_page = data.get('perPage', 20)
    
    logs_query = Log.query.filter(Log.userEmail == user_email).order_by(Log.create_time.asc())
    pagination = logs_query.paginate(page=page, per_page=per_page)
    
    result = {
      "logs": [{
        "logId": log.logId,
        "timestamp": log.create_time.strftime("%Y-%m-%d %H:%M:%S") if log.create_time else None,
        "status": log.status,
        "userEmail": log.userEmail,
        "AccessLevel": log.identity,
        "action": log.action
      } for log in pagination.items],
      "pagination": {
        "currentPage": pagination.page,
        "totalPages": pagination.pages,
        "totalItems": pagination.total
      }
    }
    
    return jsonify(result), 200
  
  except SQLAlchemyError as e:
    current_app.logger.error(f"Database error: {str(e)}")
    return jsonify({"error": "Database operation failed"}), 500
  except Exception as e:
    current_app.logger.error(f"system error: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal error of the server"}), 500
