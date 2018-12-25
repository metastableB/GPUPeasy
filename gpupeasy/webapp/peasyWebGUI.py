import os
import json
import shlex
import re
from flask import Flask, flash, redirect, jsonify, url_for
from flask import render_template, request, session, abort

from gpupeasy.core.server import GPUPeasyServer

frontend = Flask(__name__)

@frontend.route("/message")
def messageTest():
    msg = {'successMessage': 'This is a success message',
           'errorMessage': 'This is an error message',
           'infoMessage' : ' This is an info message'}
    msg = json.dumps(msg)
    return redirect(url_for('index', messages=msg))


@frontend.route("/")
def index():
    if 'messages' not in request.args:
        return render_template('index.html')
    msg = json.loads(request.args['messages'])
    return render_template('index.html', **msg)

# @frontend.route("/deviceutilization")
# def getDeviceUtilization():
    # ret = backend.getRunningJobs()
    # if len(ret) == 0:
        # return 'Empty'
    # jobs = []
    # for job in ret:
        # command = ' '.join(job.commandList)
        # gpu = job.gpu
        # jobD = {'JID': job.jobid, 'Name': job.name,
                # 'Command': command, 'gpu': gpu}
        # jobs.append(jobD)
    # return render_template('deviceutilization.html', jobs=jobs)

# @frontend.route("/scheduledjobs")
# def getScheduledJobs():
    # ret = backend.getJobsToSchedule()
    # if len(ret) == 0:
        # return 'Empty'
    # jobs = []
    # for job in ret:
        # command = ' '.join(job.commandList)
        # jobD = {'JID': job.jobid, 'Name': job.name, 'Command': command}
        # jobs.append(jobD)
    # return render_template('queue.html', jobs=jobs)

# @frontend.route("/successfuljobs")
# def getSuccessfulJobs():
    # ret = backend.getSucceededJobs()
    # if len(ret) == 0:
        # return 'Empty'
    # jobs = []
    # for job in ret:
        # command = ' '.join(job.commandList)
        # jobD = {'JID': job.jobid, 'Name': job.name, 'Command': command}
        # jobs.append(jobD)
    # return render_template('queue.html', jobs=jobs)

# @frontend.route("/failedjobs")
# def getFailedJobs():
    # ret = backend.getFailedJobs()
    # if len(ret) == 0:
        # return 'Empty'
    # jobs = []
    # for job in ret:
        # command = ' '.join(job.commandList)
        # jobD = {'JID': job.jobid, 'Name': job.name, 'Command': command}
        # jobs.append(jobD)
    # return render_template('queue.html', jobs=jobs)

# def validateJob(jobName, jobOutFile, jobCommand):
    # '''
    # returns false if error occurred along with error message.
    # Else, returns true with None as message
    # '''
    # jobOutF = jobOutFile
    # if len(jobCommand) == 0:
        # message = 'No jobs were submitted'
        # return False, message
    # if len(jobName) == 0:
        # message = 'No job name was provided'
        # return False, message
    # if len(jobOutF) == 0:
        # message = 'Output file not specified'
        # return False, message
    # if os.path.exists(jobOutF):
        # message = 'Output file already exists: %s' % jobOutF
        # return False, message
    # return True, None

# @frontend.route("/addjobs", methods=['GET', 'POST'])
# def addJobs():
    # if request.method == 'GET':
        # return render_template('addjobs.html')
    # jobCommand = request.form['jobCommand']
    # jobCommand = jobCommand.strip().replace('\n', ' ').replace('\r', ' ')
    # jobName = request.form['jobName'].strip().replace('\n', ' ')
    # jobName = jobName.replace('\r', ' ')
    # jobOutF = request.form['outputFile'].strip().replace('\n', ' ')
    # jobOutF = jobOutF.replace('\r', ' ')
    # # TODO: This should be handled in javascript
    # ret, msg = validateJob(jobName, jobOutF, jobCommand)
    # if ret is False:
        # return render_template('index.html', errMessage=msg)

    # try:
        # fp = open(jobOutF, 'w+')
    # except:
        # message = 'Could not open output file'
        # return False, message

    # jobCommand = shlex.split(jobCommand)
    # job = Job(jobName, jobCommand, stdout=fp, stderr=fp)
    # ret = backend.addNewJob(job)
    # if ret is False:
        # message = 'Could not add job. Check logs for details'
        # return render_template('index.html', errMessage=message)
    # return render_template('index.html', successMessage='Added 1 job.')


# @frontend.route("/batchaddjobs", methods=['GET', 'POST'])
# def batchAddJobs():
    # if request.method == 'GET':
        # return render_template('addjobs.html')
    # jobList = request.form['jobList'].strip()
    # jobList = jobList.replace('\n', ' ').replace('\r', ' ')
    # jobList = re.sub(' +', ' ', jobList)
    # jobList = jobList.split(';;;')
    # jobList = [x.strip() for x in jobList]
    # jobList = [x for x in jobList if len(x) > 0]
    # if len(jobList) == 0:
        # message = 'No jobs were submitted (or incorrect syntax)'
        # return render_template('index.html', errMessage=message)
    # retmsg = ''
    # countError = 0
    # for job in jobList:
        # jobS = job.split(';;')
        # jobS = [x.strip() for x in jobS]
        # jobS = [x for x in jobS if len(x) > 0]
        # if len(jobS) != 3:
            # retmsg += 'Malformed job: %s<br><br>' % job
            # countError += 1
            # continue
        # jobName, jobOutF, jobCommand = jobS[0], jobS[1], jobS[2]
        # ret, msg = validateJob(jobName, jobOutF, jobCommand)
        # if ret is False:
            # countError += 1
            # retmsg += 'Error in job: %s<br><br>' % msg
            # continue
        # try:
            # fp = open(jobOutF, 'w+')
            # fp.close()
        # except:
            # message = 'Could not open output file: %s' % jobOutF
            # retmsg += 'Error in job: %s<br><br>' % message
            # countError += 1

    # if countError != 0:
        # retmsg = 'There were %d errors. <br><br> %s' % (countError, retmsg)
        # return render_template('index.html', errMessage=retmsg)
    # sucMsg = ''
    # for job in jobList:
        # jobS = job.split(';;')
        # jobS = [x.strip() for x in jobS]
        # jobS = [x for x in jobS if len(x) > 0]
        # jobName, jobOutF, jobCommand = jobS[0], jobS[1], jobS[2]
        # try:
            # fp = open(jobOutF, 'w+')
        # except:
            # message = 'Internal error'
            # return render_template('index.html', errMessage=retmsg)

        # jobCommand = shlex.split(jobCommand)
        # jobCommand = [x.strip() for x in jobCommand]
        # print(jobCommand)
        # job = Job(jobName, jobCommand, stdout=fp, stderr=fp)
        # ret = backend.addNewJob(job)
        # if ret is False:
            # message = 'Could not add job. Check logs for details'
            # sucMg += message + '<br><br>'
    # sucMsg += 'Done'
    # return render_template('index.html', successMessage=sucMsg)

if __name__ == "__main__":
    frontend.run(debug=True, host='0.0.0.0', port='4004')
