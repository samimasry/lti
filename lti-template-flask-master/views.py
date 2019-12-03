from flask import Flask, render_template, session, request, Response
from pylti.flask import lti
import settings
import logging
import json
import requests
#
import boto3
from botocore.client import Config
#
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
    	return render_template('launchstudent.htm.j2', lis_person_name_full=session['lis_person_name_full'], student_id= session['custom_canvas_user_id'])
    
    if "Instructor" in session['roles']:
    	#launch teacher
    	return render_template('launchteacher.htm.j2', lis_person_name_full=session['lis_person_name_full'], roles=session['roles'], course_id= session['custom_canvas_course_id'])

@app.route('/studentview/<int:student_id>', methods=['POST', 'GET'])
def studentview(student_id):

	student_id = student_id


	urls= requests.get(url = "http://ec2-34-230-52-124.compute-1.amazonaws.com/ph2/videos/viewMyVideos?canvas_id="+str(student_id))
	urls = urls.json()
	numberOfUrls = len(urls['file_location'])
	#videoList = []
	 
	videoListIndices = range(0,numberOfUrls)
	session['student_video_list_urls'] =[]
	for x in range(0,numberOfUrls):
		session['student_video_list_urls'].append(urls['file_location'][x][u'file_location'])



    # Write the lti params to the console
	app.logger.info(json.dumps(request.form, indent=2))
	#app.logger.info()


	return render_template('studentview.htm.j2',urls = session['student_video_list_urls'], lis_person_name_full=session['lis_person_name_full'], videoListIndices = videoListIndices, numberOfUrls  = numberOfUrls)


@app.route('/teacherview/<int:course_id>', methods=['POST', 'GET'])
def teacherview(course_id):

	course_id = course_id

	quizzes = requests.get(url = "http://ec2-34-230-52-124.compute-1.amazonaws.com/ph2/courses/needCourseObjects?course_id=" + str(course_id))
	quizzes = quizzes.json()

	numberOfQuizzes = len(quizzes['object'])
	quizListIndices = range(1,numberOfQuizzes+1)
	session['quiz_list_based_on_course'] =[]
	for x in range(0,numberOfQuizzes):
		session['quiz_list_based_on_course'].append(quizzes['object'][x]['object'])
	#quizList = range(11,20) #get quiz list based on the course id




    # Write the lti params to the console
	app.logger.info(json.dumps(request.form, indent=2))


	return render_template('teacher_view_all_quizzes_within_course.htm.j2',quizzes = session['quiz_list_based_on_course'], numberOfQuizzes = numberOfQuizzes, quizListIndices = quizListIndices)


@app.route('/viewquiz/<int:quiz_id>', methods=['POST', 'GET'])
#@lti(error=error, request='session', role='any', app=app)
def viewquiz(quiz_id):
	quiz_id=quiz_id
	urls = requests.get(url = "http://ec2-34-230-52-124.compute-1.amazonaws.com/ph2/videos/viewMyObjectVideos?object_id="+str(quiz_id))
	urls = urls.json()
	numberOfUrls = len(urls['file_location'])
	#videoList = []
	 
	videoListIndices = range(0,numberOfUrls)
	session['teacher_video_list_urls'] =[]
	for x in range(0,numberOfUrls):
		session['teacher_video_list_urls'].append(urls['file_location'][x][u'file_location'])
	#view all videos with this quiz id
	#videoList = range(1,10)





	return render_template('viewquiz.htm.j2', urls = session['teacher_video_list_urls'],videoListIndices = videoListIndices, numberOfUrls  = numberOfUrls)

#video play page
@app.route('/viewvideo/<int:video_id>', methods=['POST', 'GET'])
#@lti(error=error, request='session', role='any', app=app)
def viewvideo(video_id):
	video_id=video_id
	#below keys and secret should not be hardcode
	s3 = boto3.client('s3', config=Config(signature_version='s3v4') ,
		aws_access_key_id = "AKIAXRDTGP6FG7XNDPEZ",
		aws_secret_access_key = "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",
		)

	# Generate the URL to get 'key-name' from 'bucket-name'
	# URL expires in 604800 seconds (seven days)
	url = s3.generate_presigned_url(
    ClientMethod='get_object',
    Params={
        'Bucket': 'rekogtest-akane',
        'Key': session['student_video_list_urls'][video_id-1].replace("https://rekogtest-akane.s3.amazonaws.com/","")
    },
    ExpiresIn=604800
)






	return render_template('viewvideo.htm.j2', key = session['student_video_list_urls'][video_id-1].replace("https://rekogtest-akane.s3.amazonaws.com/",""), url = url)


#video teacher page
@app.route('/viewvideoandflags/<int:teacher_video_id>', methods=['POST', 'GET'])
#@lti(error=error, request='session', role='any', app=app)
def viewvideoandflags(teacher_video_id):
	teacher_video_id=teacher_video_id
	#below keys and secret should not be hardcoded
	s3 = boto3.client('s3', config=Config(signature_version='s3v4') ,
		aws_access_key_id = "AKIAXRDTGP6FG7XNDPEZ",
		aws_secret_access_key = "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",
		)

	# Generate the URL to get 'key-name' from 'bucket-name'
	# URL expires in 604800 seconds (seven days)
	url = s3.generate_presigned_url(
    ClientMethod='get_object',
    Params={
        'Bucket': 'rekogtest-akane',
        'Key': session['teacher_video_list_urls'][teacher_video_id-1].replace("https://rekogtest-akane.s3.amazonaws.com/","")
    },
    ExpiresIn=604800
)
	#########################################################################################
	#Note: add flags + logged sites here
	s3 = boto3.client('s3', config=Config(signature_version='s3v4') ,
		aws_access_key_id = "AKIAXRDTGP6FG7XNDPEZ",
		aws_secret_access_key = "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",
		)

	# Generate the URL to get 'key-name' from 'bucket-name'
	# URL expires in 604800 seconds (seven days)
	txtUrl = s3.generate_presigned_url(
    ClientMethod='get_object',
    Params={
        'Bucket': 'rekogtest-akane',
        'Key': '2019-12-2+10%3A18%3A53.txt'
    },
    ExpiresIn=604800
)







	return render_template('viewvideoandflags.htm.j2', key = session['teacher_video_list_urls'][teacher_video_id-1].replace("https://rekogtest-akane.s3.amazonaws.com/",""), url = url, txtUrl = txtUrl)
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
