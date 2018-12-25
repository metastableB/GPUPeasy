import os
import json
import shlex
import re
from flask import Flask, flash, redirect, jsonify, url_for
from flask import render_template, request, session, abort
import requests

from gpupeasy.core.server import GPUPeasyServer


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

class GPUSchedulerGUI:
    def __init__(self, coreHost, corePort, debug=False):
        self.__frontend = Flask(__name__)
        self.__cHost = coreHost
        self.__cPort = corePort
        self.__debug = debug

        fe = self.__frontend
        fe.add_url_rule('/message', 'messageTest',
                        self.__messageTest)
        fe.add_url_rule('/', 'index', self.__index)
        fe.add_url_rule('/deviceutilization', 'getDeviceUtilization',
                        self.__getDeviceUtilization)

    def __makeCoreRequest(self, url, method):
        '''
        Returns: Response, message
            Response is None in the event of an error and an error message will
            be provided as message.
        '''
        assert method in ['GET', 'PORT'], 'Invalid method: %s' % method
        func = requests.post
        if method == 'GET':
            func = requests.get
        try:
            resp = func(url)
        except requests.ConnectionError:
            return None, 'Connection error on url: %s' % url
        except requests.Timeout:
            return None, 'Connection timeout on url: %s' % url
        except requests.TooManyRedirects:
            return None, 'Too many redirects on url: %s' % url
        return resp, None

    # URL end-points
    def __messageTest(self):
        msg = {'successMessage': 'This is a success message',
               'errorMessage': 'This is an error message',
               'infoMessage' : ' This is an info message'}
        msg = json.dumps(msg)
        return redirect(url_for('index', messages=msg))

    def __index(self):
        if 'messages' not in request.args:
            return render_template('index.html')
        msg = json.loads(request.args['messages'])
        return render_template('index.html', **msg)

    def __getDeviceUtilization(self):
        '''
        Returns template
        '''
        url = 'http://%s:%s/deviceutilization' % (self.__cHost, self.__cPort)
        utilization, msg = self.__makeCoreRequest(url, method='GET')
        if utilization is None:
            return render_template('deviceutilization.html', errorMessage=msg)

        url = 'http://%s:%s/availabledevices' % (self.__cHost, self.__cPort)
        allDiv, msg = self.__makeCoreRequest(url, method='GET')
        if allDiv is None:
            return render_template('deviceutilization.html', errorMessage=msg)

        utilization = utilization.json()
        print(utilization)
        allDiv = allDiv.json()
        if utilization['status'] != 'successful':
            msg = 'Could not fetch utilization info from core server'
            return render_template('deviceutilization.html', errorMessage=msg)
        if allDiv['status'] != 'successful':
            msg = 'Could not fetch all devices info from core server'
            return render_template('deviceutilization.html', errorMessage=msg)

        ret = {}
        for gpu in allDiv['value']:
            ret[gpu] = {'name': gpu, 'idle': True, 'job': {}}

        for job in utilization['value']:
            gpu = job['gpu']
            # GPU should be key
            assert gpu in ret, 'Internal error. Invalid invariant'
            # not two jobs should be scheduled on a GPU
            assert ret[gpu]['idle'] == True, 'Internal error. Invalid invariant'
            ret[gpu]['job'] = job
            ret[gpu]['idle'] = False
        return render_template('deviceutilization.html', devices=ret)

    def run(self, host, port):
        self.__frontend.run(debug=self.__debug, host=host, port=port)




if __name__ == "__main__":
    frontend = GPUSchedulerGUI('localhost', '8888', debug=True)
    frontend.run(host='0.0.0.0', port='4004')
