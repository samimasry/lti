from flask import Flask, render_template, session, request, Response
from pylti.flask import lti
import settings
import logging
import json
import requests
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.secret_key = settings.secret_key
app.config.from_object(settings.configClass)


# ============================================
# Logging
# ============================================

formatter = logging.Formatter(settings.LOG_FORMAT)
handler = RotatingFileHandler(
    settings.LOG_FILE,
    maxBytes=settings.LOG_MAX_BYTES,
    backupCount=settings.LOG_BACKUP_COUNT
)
handler.setLevel(logging.getLevelName(settings.LOG_LEVEL))
handler.setFormatter(formatter)
app.logger.addHandler(handler)


# ============================================
# Utility Functions
# ============================================

def return_error(msg):
    return render_template('error.htm.j2', msg=msg)


def error(exception=None):
    app.logger.error("PyLTI error: {}".format(exception))
    return return_error('''Authentication error,
        please refresh and try again. If this error persists,
        please contact support.''')


# ============================================
# Web Views / Routes
# ============================================

# LTI Launch
@app.route('/launch', methods=['POST', 'GET'])
@lti(error=error, request='initial', role='any', app=app)
def launch(lti=lti):
    """
    Returns the launch page
    request.form will contain all the lti params
    """

    # example of getting lti data from the request
    # let's just store it in our session
    session['lis_person_name_full'] = request.form.get('lis_person_name_full')
    session['custom_canvas_user_id'] = request.form.get('custom_canvas_user_id')
    session['roles'] = request.form.get('roles')
    session['custom_canvas_course_id'] = request.form.get('custom_canvas_course_id')
    #take the user id and fetch all their recorded videos

    #videoList = range(1,10) #get video list
    #student = "no" # if student


    #assume we have three videos videoid63 videoid65 videoid64
    #videos = ["videoid65", "videoid63", "videoid64"]
    #if teacher quiz list



    # Write the lti params to the console
    app.logger.info(json.dumps(request.form, indent=2))

    if "Learner" in session['roles']:
    	#launch student
    	return render_template('launchstudent.htm.j2', lis_person_name_full=session['lis_person_name_full'], roles=session['roles'], student_id= session['custom_canvas_user_id'])
    
    if "Instructor" in session['roles']:
    	#launch teacher
    	return render_template('launchteacher.htm.j2', lis_person_name_full=session['lis_person_name_full'], roles=session['roles'], course_id= session['custom_canvas_course_id'])

@app.route('/studentview/<int:student_id>', methods=['POST', 'GET'])
def studentview(student_id):

	student_id = student_id


	urls= requests.get(url = "http://ec2-34-230-52-124.compute-1.amazonaws.com/ph2/videos/viewMyVideos?canvas_id=34")
	urls = urls.json()
	urls = urls['file_location']
	videoList = []

	for url in urls:
		videoList.append(url['file_location'].encode('ascii','ignore'))

	 #get video list based on the studentid



    # Write the lti params to the console
	app.logger.info(json.dumps(request.form, indent=2))
	#app.logger.info()


	return render_template('studentview.htm.j2',urls = urls,  lis_person_name_full=session['lis_person_name_full'], videoList = videoList, roles=session['roles'], student_id = student_id)


@app.route('/teacherview/<int:course_id>', methods=['POST', 'GET'])
def teacherview(course_id):

	course_id = course_id

	quizList = range(11,20) #get quiz list based on the course id



    # Write the lti params to the console
	app.logger.info(json.dumps(request.form, indent=2))


	return render_template('teacher_view_all_quizzes_within_course.htm.j2', lis_person_name_full=session['lis_person_name_full'], quizList = quizList, roles=session['roles'])


@app.route('/viewquiz/<int:quiz_id>', methods=['POST', 'GET'])
#@lti(error=error, request='session', role='any', app=app)
def viewquiz(quiz_id):
	quiz_id=quiz_id
	#view all videos with this quiz id
	videoList = range(1,10)





	return render_template('viewquiz.htm.j2', videoList = videoList)

#video play page
@app.route('/viewvideo/<string:video_id>', methods=['POST', 'GET'])
#@lti(error=error, request='session', role='any', app=app)
def viewvideo(video_id):
	video_id=video_id





	return render_template('viewvideo.htm.j2', video_id=video_id)


# Home page
@app.route('/', methods=['GET'])
def index(lti=lti):
    return render_template('index.htm.j2')


# LTI XML Configuration
@app.route("/xml/", methods=['GET'])
def xml():
    """
    Returns the lti.xml file for the app.
    XML can be built at https://www.eduappcenter.com/
    """
    try:
        return Response(render_template(
            'lti.xml.j2'), mimetype='application/xml'
        )
    except:
        app.logger.error("Error with XML.")
        return return_error('''Error with XML. Please refresh and try again. If this error persists,
            please contact support.''')
