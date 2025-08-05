from flask import Blueprint, render_template

frontendBP = Blueprint('frontend', __name__)

@frontendBP.route('/login')
def show_login_page():
    return render_template('login.html')

#Data User
@frontendBP.route('/course-view')
def course_view():
    return render_template('Data User/course-view.html')

@frontendBP.route('/policy-view')
def policy_view():
    return render_template('Data User/policy-view.html')

@frontendBP.route('/private-data-consumer')
def private_data_consumer():
    return render_template('Data User/private-data-consumer.html')

@frontendBP.route('/private-data-provider')
def private_data_provider():
    return render_template('Data User/private-data-provider.html')

@frontendBP.route('/provide-course')
def provide_course():
    return render_template('Data User/provide-course.html')

@frontendBP.route('/provide-database-api')
def provide_database_api():
    return render_template('Data User/provide-database-api.html')

@frontendBP.route('/public-data-consumer')
def public_data_consumer():
    return render_template('Data User/public-data-consumer.html')

@frontendBP.route('/student-check')
def student_check():
    return render_template('Data User/student-check.html')

@frontendBP.route('/student-info-check')
def student_info_check():
    return render_template('Data User/student-info-check.html')

@frontendBP.route('/submit-question')
def submit_question():
    return render_template('Data User/submit-question.html')

@frontendBP.route('/thesis')
def thesis():
    return render_template('Data User/thesis.html')

#E-Admin
@frontendBP.route('/edba-bank-account')
def edba_bank_account():
    return render_template('E-Admin/edba-bank-account.html')

@frontendBP.route('/eadmin')
def eadmin():
    return render_template('E-Admin/eadmin.html')

@frontendBP.route('/editorial-policy')
def editorial_policy():
    return render_template('E-Admin/editorial-policy.html')

@frontendBP.route('/membership-fee')
def membership_fee():
    return render_template('E-Admin/membership-fee.html')

@frontendBP.route('/registration-process')
def registration_process():
    return render_template('E-Admin/registration-process.html')

@frontendBP.route('/system-log')
def system_log():
    return render_template('E-Admin/system-log.html')

#O-Convener
@frontendBP.route('/bank-account-input')
def bank_account_input():
    return render_template('O-Convener/bank-account-input.html')

@frontendBP.route('/edit-member')
def edit_member():
    return render_template('O-Convener/edit-member.html')

@frontendBP.route('/oconvener')
def oconvener():
    return render_template('O-Convener/oconvener.html')

@frontendBP.route('/organization-log')
def organization_log():
    return render_template('O-Convener/organization-log.html')

@frontendBP.route('/register')
def register():
    return render_template('O-Convener/register.html')

@frontendBP.route('/set-service')
def set_service():
    return render_template('O-Convener/set-service.html')

#Senior-E-Admin
@frontendBP.route('/senior-eadmin')
def senior_eadmin():
    return render_template('Senior-E-Admin/senior-eadmin.html')

@frontendBP.route('/senior-registration-process')
def senior_registration_process():
    return render_template('Senior-E-Admin/senior-registration-process.html')

#T-Admin
@frontendBP.route('/question-answering')
def question_answering():
    return render_template('T-Admin/question-answering.html')

@frontendBP.route('/set-admin')
def set_admin():
    return render_template('T-Admin/set-admin.html')

@frontendBP.route('/tadmin')
def tadmin():
    return render_template('T-Admin/tadmin.html')

