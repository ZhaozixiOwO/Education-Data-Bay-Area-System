import json
import requests
from app.models.apiConfig import API
from app.models.base import db
from app.models.course import Course
from app.models.datauser import DataUser
from app.models.oconvener import OConvener
from app.models.workspace import Workspace
from flask import Blueprint, request, jsonify, Response

datauserBP = Blueprint('datauser', __name__)


def is_duplicate_record(apiUrl, apiPath, apiMethod, oName):
  # Find out if there are records of the same combination of URL, Path, Method, Input and Output
  existing_record = db.session.query(API).filter(
    API.organizationName == oName,
    API.base_url == apiUrl,
    API.path == apiPath,
    API.method == apiMethod,
    API.status != 0
  ).first()
  return existing_record is not None


@datauserBP.route('/get_workspace_status1', methods=['GET'])
def get_workspace_status1():
  try:
    # Retrieve the user_id of the current login from the session
    user_id = request.args.get('userId')
    if not user_id:
      return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
    
    data_user = db.session.query(DataUser).filter_by(userId=user_id).first()
    if not data_user:
      return jsonify({"error": "The corresponding DataUser cannot be found"}), 406
    
    convenerId = data_user.convenerId
    
    workspaces = db.session.query(Workspace).filter_by(convenerId=convenerId, status=1).all()
    
    if not workspaces:
      return jsonify({"error": "There are no services to be configured"}), 404
    
    result = [{
      "serviceId": w.id,
      "service": w.service
    } for w in workspaces]
    
    return jsonify(result), 200
  
  except Exception as e:
    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500


@datauserBP.route('/config', methods=['POST'])
def config():
  try:
    user_id = request.args.get('userId')
    if not user_id:
      return jsonify({"error": "The user is not logged in or the session is invalid"}), 401
    
    data_user = db.session.query(DataUser).filter_by(userId=user_id).first()
    if not data_user:
      return jsonify({"error": "The corresponding DataUser cannot be found"}), 406
    
    convenerId = data_user.convenerId
    oc = db.session.query(OConvener).filter_by(convenerId=convenerId).first()

    apiUrl = request.form.get('apiUrl')
    apiPath = request.form.get('apiPath')
    apiMethod = request.form.get('apiMethod')
    apiInput = request.form.get('apiInput')
    apiOutput = request.form.get('apiOutput')
    apiCategory = request.form.get('apiCategory')
    if not all([apiUrl, apiPath, apiMethod, apiInput, apiOutput, apiCategory]):
      return jsonify({"error": "Lack of necessary parameters"}), 400
    
    # Determine whether there are duplicate records
    existing_config = db.session.query(API).filter_by(
      organizationName=oc.organizationName,
      portContent=apiCategory
    ).first()
    if existing_config:
      existing_config.base_url = apiUrl
      existing_config.path = apiPath
      existing_config.method = apiMethod
      existing_config.input = json.loads(apiInput)
      existing_config.output = json.loads(apiOutput)
      existing_config.organizationName = oc.organizationName
      db.session.commit()
      return jsonify({
        "message": "The configuration was updated successfully.",
        "config_id": existing_config.id
      }), 200
    # Determine whether there are duplicate records
    else:
      new_config = API(
        institution_id=convenerId,
        base_url=apiUrl,
        path=apiPath,
        method=apiMethod,
        input=json.loads(apiInput),
        output=json.loads(apiOutput),
        organizationName=oc.organizationName,
        portContent=apiCategory
      )
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


@datauserBP.route('/test_config_connection', methods=['POST'])
def test_config_connection():
  try:
    data = request.get_json()
    service_id = data.get("serviceId")
    success = data.get("success")

    if success:
      workspace = db.session.query(Workspace).filter_by(id=service_id).first()
      
      if workspace:
        workspace.status = 0
        db.session.commit()
      
      return jsonify({"success": True, "message": "The connection was successful and the status has been updated"}), 200
    else:
      return jsonify({"success": False, "error": "Update failed"}), 500
  except Exception as e:
    return jsonify({"success": False, "error": str(e)}), 500


@datauserBP.route('/api/test_organizationName', methods=['GET'])
def test_organizationName():
  user_id = request.args.get("userId")
  datauser = db.session.query(DataUser).filter_by(userId=user_id).first()
  oconvener = db.session.query(OConvener).filter_by(convenerId=datauser.convenerId).first()
  organization_list = []
  if oconvener:
    organization_list.append({
      "organizationName": oconvener.organizationName
    })
  

  return jsonify(organization_list)


@datauserBP.route('/api/send_student_info_names', methods=['GET'])
def send_student_info_names():
  workspaces = db.session.query(Workspace).filter(Workspace.service == "student info", Workspace.status == 2).all()
  
  organization_list = []
  for workspace in workspaces:
    oconvener = db.session.query(OConvener).filter_by(convenerId=workspace.convenerId).first()
    
    if oconvener:
      organization_list.append({
        "organizationName": oconvener.organizationName
      })
  

  return jsonify(organization_list)


@datauserBP.route('/api/get_student_info_names', methods=['GET'])
def get_student_info_names():
  name = request.args.get('name')
  
  if name:
    api = db.session.query(API).filter(
      API.organizationName == name,
      API.portContent == "student info"
    ).first()
    if not api:
      return jsonify({"error": "Organization not found"}), 405
    
    try:
      inputs = api.input

    except Exception:
      inputs = {}
    return jsonify(inputs), 200
  
  else:
    names = db.session.query(API.organizationName).all()
    organization_list = [name[0] for name in names]
    return jsonify(organization_list), 200


@datauserBP.route('/api/student_info_check', methods=['POST'])
def student_info_check():
  try:
    data = request.get_json()
    org_name = request.args.get('name')
    
    api = db.session.query(API).filter_by(organizationName=org_name, portContent="student info").first()
    if not api:
      return jsonify({"error": "Organization not found"}), 404
    
    base_url = api.base_url
    path = api.path
    method = api.method
    inputs = api.input
    
    url = base_url + path

    final_payload = {}
    for key in inputs.keys():
      final_payload[key] = data.get(key, "")
    
    try:
      if method.lower() == 'post':
        response = requests.post(url, json=final_payload, timeout=5)
      elif method.lower() == 'get':
        response = requests.get(url, params=final_payload, timeout=5)
      else:
        return jsonify({"error": "Unsupported HTTP method"}), 400
    except requests.exceptions.RequestException as e:
      return jsonify({"error": "Failed to call external API", "details": str(e)}), 502
    
    try:
      response_data = response.json()
    except ValueError:
      response_data = response.text
    
    outputs = api.output
    adapted_response = {}
    if isinstance(outputs, dict) and isinstance(response_data, dict):
      missing_keys = []
      for key in outputs.keys():
        if key not in response_data:
          missing_keys.append(key)
        adapted_response[key] = response_data.get(key, "")
      
      if missing_keys == list(outputs.keys()):
        # If all the expected fields are missing
        return jsonify({
          "success": True,
          "error": "No student information was found",
          "details": adapted_response
        }), 200
    
    else:
      adapted_response = response_data
    
    return jsonify({
      "success": True,
      "data": adapted_response
    }), 200
  
  except Exception as e:

    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500


@datauserBP.route('/api/send_student_check_names', methods=['GET'])
def send_student_check_names():
  workspaces = db.session.query(Workspace).filter(Workspace.service == "student check", Workspace.status == 2).all()
  
  organization_list = []
  for workspace in workspaces:

    oconvener = db.session.query(OConvener).filter_by(convenerId=workspace.convenerId).first()

    if oconvener:
      organization_list.append({
        "organizationName": oconvener.organizationName
      })
  
  return jsonify(organization_list)


@datauserBP.route('/api/get_student_check_names', methods=['GET'])
def get_student_check_names():
  name = request.args.get('name')
  
  if name:
    api = db.session.query(API).filter(
      API.organizationName == name,
      API.portContent == "student check"
    ).first()
    if not api:
      return jsonify({"error": "Organization not found"}), 405
    
    try:
      inputs = api.input
    except Exception:
      inputs = {}
    return jsonify(inputs), 200
  
  else:
    names = db.session.query(API.organizationName).all()
    organization_list = [name[0] for name in names]
    return jsonify(organization_list), 200


@datauserBP.route('/api/student_check', methods=['POST'])
def student_check():
  try:

    data = request.get_json()
    org_name = request.args.get('name')
    
    
    api = db.session.query(API).filter_by(organizationName=org_name, portContent="student check").first()

    if not api:
      return jsonify({"error": "Organization not found"}), 404

    base_url = api.base_url
    path = api.path
    method = api.method
    inputs = api.input
    
    url = base_url + path

    final_payload = {}
    for key in inputs.keys():
      final_payload[key] = data.get(key, "")
    
    
    try:
      if method.lower() == 'post':
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, data=final_payload, headers=headers, timeout=5)
      elif method.lower() == 'get':
        response = requests.get(url, params=final_payload, timeout=5)
      else:
        return jsonify({"error": "Unsupported HTTP method"}), 400
    except requests.exceptions.RequestException as e:
      return jsonify({"error": "Failed to call external API", "details": str(e)}), 502
    
    try:
      response_data = response.json()
    except ValueError:
      response_data = response.text
    
    outputs = api.output
    adapted_response = {}
    if isinstance(outputs, dict) and isinstance(response_data, dict):
      missing_keys = []
      for key in outputs.keys():
        if key not in response_data:
          missing_keys.append(key)
        adapted_response[key] = response_data.get(key, "")
      
      if missing_keys == list(outputs.keys()):
        return jsonify({
          "success": True,
          "error": "No student information was found",
          "details": response_data
        }), 200
    
    else:
      adapted_response = response_data
    

    return jsonify({
      "success": True,
      "data": adapted_response
    }), 200
  
  except Exception as e:

    return jsonify({"error": "Internal error of the server", "details": str(e)}), 500


@datauserBP.route('/api/batch_student_check', methods=['POST'])
def batch_student_check():
  try:
    file = request.files['file']
    org_name = request.args.get('name')
    if not file or not org_name:
      return jsonify({"error": "The file or organization name is missing"}), 400
    
    import pandas as pd
    df = pd.read_excel(file)
    
    api = db.session.query(API).filter_by(organizationName=org_name, portContent="student check").first()
    if not api:
      return jsonify({"error": "The corresponding interface configuration cannot be found"}), 404
    
    results = []
    for _, row in df.iterrows():
      payload = {}
      for key in api.input.keys():
        payload[key] = row.get(key, "")
      
      try:
        if api.method.lower() == 'post':
          response = requests.post(api.base_url + api.path, data=payload, timeout=5)
        else:
          response = requests.get(api.base_url + api.path, params=payload, timeout=5)
        try:
          result_data = response.json()
        except:
          result_data = response.text
        results.append({"input": payload, "result": result_data})
      except Exception as e:
        results.append({"input": payload, "error": str(e)})
    
    return jsonify(results), 200
  except Exception as e:
    return jsonify({"error": "An error occurred in handling batch checks", "details": str(e)}), 500


@datauserBP.route('/api/send_thesis_info_names', methods=['GET'])
def send_thesis_info_names():
  workspaces = db.session.query(Workspace).filter(Workspace.service.in_(['thesis', 'thesis_download']),
                                                  Workspace.status == 2).all()
  
  organization_list = []
  for workspace in workspaces:
    oconvener = db.session.query(OConvener).filter_by(convenerId=workspace.convenerId).first()
    
    if oconvener:
      organization_list.append({
        "organizationName": oconvener.organizationName,
        "portContent": workspace.service
      })
  
  return jsonify(organization_list)


@datauserBP.route('/api/get_thesis_info_names', methods=['GET'])
def get_thesis_info_names():
  name = request.args.get('name')
  port_content = request.args.get('portContent')
  if name and port_content:
    api = db.session.query(API).filter_by(organizationName=name, portContent=port_content).first()
    if not api:
      return jsonify({"error": "Organization not found"}), 405
    
    try:
      inputs = api.input
    except Exception:
      inputs = {}
    return jsonify(inputs), 200
  
  else:
    names = db.session.query(API.organizationName).all()
    organization_list = [name[0] for name in names]
    return jsonify(organization_list), 200


@datauserBP.route('/api/thesis_info_check', methods=['POST'])
def thesis_info_check():
  try:
    data = request.get_json()
    org_name = request.args.get('name')
    port_content = request.args.get('portContent')

    api = db.session.query(API).filter_by(organizationName=org_name, portContent=port_content).first()
    if not api:
      return jsonify({"error": "Organization not found"}), 404

    base_url = api.base_url
    path = api.path
    method = api.method
    inputs = api.input
    
    url = base_url + path

    
    final_payload = {}
    for key in inputs.keys():
      final_payload[key] = data.get(key, "")
    

    try:
      if method.lower() == 'post':
        response = requests.post(url, json=final_payload, timeout=5)
      elif method.lower() == 'get':
        response = requests.get(url, params=final_payload, timeout=5)
      else:
        return jsonify({"error": "Unsupported HTTP method"}), 400
    except requests.exceptions.RequestException as e:
      return jsonify({"error": "Failed to call external API", "details": str(e)}), 502
    
    content_type = response.headers.get('Content-Type', '')
    content = response.content
    
    if 'application/pdf' in content_type or content.startswith(b'%PDF'):
      return Response(
        content,
        mimetype='application/pdf',
        headers={
          'Content-Disposition': 'attachment; filename="thesis.pdf"',
          'success': 'true'
        }
      )
    
    try:
      response_data = response.json()
    except ValueError:
      response_data = response.text
    
    outputs = api.output
    
    adapted_response = []
    if isinstance(response_data, list):
      for entry in response_data:
        adapted_entry = {}
        for key in outputs.keys():
          if key in entry:
            adapted_entry[key] = entry[key]
        adapted_response.append(adapted_entry)
    else:
      adapted_response = response_data
    
    return jsonify({
      "success": True,
      "data": adapted_response
    }), 200
  
  
  except Exception as e:
    return jsonify({"error": "Server Internal Error", "details": str(e)}), 500


@datauserBP.route('/api/get_workspace_price', methods=['GET'])
def get_workspace_price():
  org_name = request.args.get('name')
  portContent = request.args.get('portContent')
  if not org_name or not portContent:
    return jsonify({"error": "The 'name' parameter is missing"}), 400
  

  oc = db.session.query(OConvener).filter_by(organizationName=org_name).first()
  workspace = db.session.query(Workspace).filter_by(convenerId=oc.convenerId, service=portContent).first()
  
  if not workspace:
    return jsonify({"error": "The corresponding Workspace couldn't be found"}), 404
  
  return jsonify({"price": workspace.price}), 200


@datauserBP.route('/list_courses', methods=['GET'])
def list_courses():
  try:
    user_id = request.args.get('userId')
    if not user_id:
      return jsonify({"success": False, "message": "The userId parameter is missing"}), 400
    
    datauser = db.session.query(DataUser).filter_by(userId=user_id).first()
    if not datauser:
      return jsonify({"success": False, "message": "The data user couldn't be found"}), 404
    oconvener = db.session.query(OConvener).filter_by(convenerId=datauser.convenerId).first()
    active_course_service = db.session.query(Workspace).filter_by(
      convenerId=oconvener.convenerId,
      service="course",
      status=2
    ).first()
    if not active_course_service:
      return jsonify({"success": False, "message": "Please activate and enable the Course service first"}), 403
    
    courses = db.session.query(Course).filter_by(convenerId=oconvener.convenerId).all()
    result = []
    for course in courses:
      result.append({
        'courseId': course.courseId,
        'title': course.title,
        'description': course.description,
        'organizationName': oconvener.organizationName,
        'instructor': course.instructor,
        'credits': course.credits or 0
      })
    
    return jsonify({"success": True, "data": result}), 200
  
  except Exception as e:
    return jsonify({"success": False, "message": f"Failed to obtain the course: {str(e)}"}), 500


@datauserBP.route('/add_course', methods=['POST'])
def add_course():
  try:
    user_id = request.args.get('userId')
    data = request.get_json()
    
    if not user_id or not data.get("title"):
      return jsonify({"success": False, "message": "Lack of necessary parameters"}), 400
    
    datauser = db.session.query(DataUser).filter_by(userId=user_id).first()
    if not datauser:
      return jsonify({"success": False, "message": "The data user couldn't be found"}), 404
    oconvener = db.session.query(OConvener).filter_by(convenerId=datauser.convenerId).first()
    if not oconvener:
      return jsonify({"success": False, "message": "The corresponding organization cannot be found"}), 404
    active_course_service = db.session.query(Workspace).filter_by(
      convenerId=oconvener.convenerId,
      service="course",
      status=2
    ).first()
    if not active_course_service:
      return jsonify({"success": False, "message": "The Course service has not been enabled yet"}), 403
    
    new_course = Course(
      title=data.get("title"),
      description=data.get("description"),
      instructor=data.get("instructor"),
      credits=data.get("credits"),
      convenerId=oconvener.convenerId,
    )
    db.session.add(new_course)
    db.session.commit()
    return jsonify({"success": True, "message": "The course was added successfully."}), 201
  
  except Exception as e:
    db.session.rollback()
    return jsonify({"success": False, "message": f"Failed to add the course: {str(e)}"}), 500


@datauserBP.route('/edit_course', methods=['POST'])
def edit_course():
  try:
    course_id = request.args.get('courseId')
    data = request.get_json()
    
    if not course_id:
      return jsonify({"success": False, "message": "The 'courseId'' parameter is missing"}), 400
    
    course = db.session.query(Course).filter_by(courseId=course_id).first()
    if not course:
      return jsonify({"success": False, "message": "The course does not exist."}), 404
    
    course.title = data.get("title", course.title)
    course.description = data.get("description", course.description)
    course.instructor = data.get("instructor", course.instructor)
    course.credits = data.get("credits", course.credits)
    
    db.session.commit()
    return jsonify({"success": True, "message": "The course update was successful."}), 200
  
  except Exception as e:
    db.session.rollback()
    return jsonify({"success": False, "message": f"The course update was failed.: {str(e)}"}), 500


@datauserBP.route('/show_courses', methods=['GET'])
def show_courses():
  try:
    organizationName = request.args.get('organizationName')
    
    if organizationName:
      oconvener = OConvener.query.filter_by(organizationName=organizationName).first()
      courses = Course.query.filter_by(convenerId=oconvener.convenerId).all()
    else:
      courses = Course.query.all()
    
    result = []
    for course in courses:
      result.append({
        'courseId': course.courseId,
        'title': course.title,
        'description': course.description,
        'organizationName': organizationName,
        'instructor': course.instructor,
        'credits': course.credits
      })
    
    return jsonify({
      'success': True,
      'data': result
    }), 200
  
  except Exception as e:
    return jsonify({
      'success': False,
      'message': f'Failed to obtain the course list: {str(e)}'
    }), 400


@datauserBP.route('/get_organization_names', methods=['GET'])
def get_organization_names():
  try:
    organizationName = db.session.query(OConvener.organizationName).distinct().all()
    result = [{"name": org[0]} for org in organizationName]
    return jsonify(result), 200
  except Exception as e:
    return jsonify({
      "error": "Failure to obtain the organization",
      "details": str(e)
    }), 500


@datauserBP.route('/list_public_courses', methods=['GET'])
def list_public_courses():
  keyword = request.args.get('keyword', '').strip()
  subquery = db.session.query(Workspace.convenerId).filter(
    Workspace.service == "Course",
    Workspace.status == 2
  ).subquery()
  query = db.session.query(Course).filter(Course.convenerId.in_(subquery))
  if keyword:
    query = query.filter(Course.title.ilike(f'%{keyword}%'))
  
  courses = query.all()
  result = [{
    "courseId": c.courseId,
    "title": c.title,
    "description": c.description,
    "instructor": c.instructor,
    "credits": c.credits
  } for c in courses]
  
  return jsonify({"success": True, "data": result}), 200
