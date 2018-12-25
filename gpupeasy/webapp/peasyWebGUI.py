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
        fe.add_url_rule('/batchaddjobs', 'batchAddJobs', self.__batchAddJobs,
                        methods=['GET', 'POST'])

    def __makeCoreRequest(self, url, method, data=None):
        '''
        Returns: Response, message
            Response is None in the event of an error and an error message will
            be provided as message.
        '''
        assert method in ['GET', 'POST'], 'Invalid method: %s' % method
        try:
            if method == 'GET':
                resp = requests.get(url)
            elif method == 'POST':
                resp = requests.post(url, json=data)
        except requests.ConnectionError:
            return None, 'Connection error on url: %s' % url
        except requests.Timeout:
            return None, 'Connection timeout on url: %s' % url
        except requests.TooManyRedirects:
            return None, 'Too many redirects on url: %s' % url
        return resp, None

    def __validateJob(self, jobName, jobOutFile, jobCommand):
        '''
        returns false if error occurred along with error message.
        Else, returns true with None as message
        '''
        jobOutF = jobOutFile
        if len(jobCommand) == 0:
            message = 'No jobs were submitted'
            return False, message
        if len(jobName) == 0:
            message = 'No job name was provided'
            return False, message
        if len(jobOutF) == 0:
            message = 'Output file not specified'
            return False, message
        if os.path.exists(jobOutF):
            message = 'Output file already exists or common'
            message += ' to multiple jobs: %s' % jobOutF
            return False, message
        return True, None

    def __addJob(self, jobName, jobOutfile, jobCommand):
        js = {
            'job':{
                'jobName': jobName,
                'outFile': jobOutfile,
                'jobCommand': jobCommand
            }
        }
        url = 'http://%s:%s/addnewjob' % (self.__cHost, self.__cPort)
        return self.__makeCoreRequest(url, method='POST', data=js)

    # URL end-points
    def __messageTest(self):
        msg = {'successMessage': 'This is a success message',
               'errorMessage': 'This\n\nis an error message',
               'infoMessage' : 'This\n\nis an info message'}
        msg = json.dumps(msg)
        return redirect(url_for('index', messages=msg))

    def __index(self):
        if 'messages' not in request.args:
            return render_template('index.html')
        msg = json.loads(request.args['messages'])
        for key in msg:
            value = msg[key]
            value = value.strip()
            print(value)
            value = value.replace('\n', '<br \>')
            print(value)
            print()
            msg[key] = value
        return render_template('index.html', **msg)

    def __batchAddJobs(self):
        if request.method == 'GET':
            return render_template('addjobs.html')

        jobList = request.form['jobList'].strip()
        jobList = jobList.replace('\n', ' ').replace('\r', ' ')
        jobList = re.sub(' +', ' ', jobList)
        jobList = jobList.split(';;;')
        jobList = [x.strip() for x in jobList]
        jobList = [x for x in jobList if len(x) > 0]
        if len(jobList) == 0:
            message = 'No jobs were submitted (or incorrect syntax)'
            msg = {'errorMessage': message}
            return redirect(url_for('index', messages=json.dumps(msg)))
        retmsg = ''
        countError = 0
        for job in jobList:
            jobS = job.split(';;')
            jobS = [x.strip() for x in jobS]
            jobS = [x for x in jobS if len(x) > 0]
            if len(jobS) != 3:
                retmsg += 'Malformed job: %s\n\n'% job
                countError += 1
                continue
            jobName, jobOutF, jobCommand = jobS[0], jobS[1], jobS[2]
            ret, msg = self.__validateJob(jobName, jobOutF, jobCommand)
            if ret is False:
                countError += 1
                retmsg += 'Error in job: %s: %s\n\n' % (jobName, msg)
                continue

        if countError != 0:
            retmsg = 'There were %d errors. \n\n%s' % (countError, retmsg)
            msg = {'errorMessage': retmsg}
            return redirect(url_for('index', messages=json.dumps(msg)))
        sucMsg = 'Jobs successfully passed onto scheduler\n.'
        for job in jobList:
            jobS = job.split(';;')
            jobS = [x.strip() for x in jobS]
            jobS = [x for x in jobS if len(x) > 0]
            jobName, jobOutF, jobCommand = jobS[0], jobS[1], jobS[2]
            jobCommand = shlex.split(jobCommand)
            jobCommand = [x.strip() for x in jobCommand]

            resp, msg = self.__addJob(jobName, jobOutF, jobCommand)
            if resp is None:
                message = 'Could not add job: %s. Scheduler' % jobName
                message += ' Scheduler returned error '
                message += 'message: %s' % (msg)
                sucMsg += message + '\n\n'
            status, msg = resp.json()['status'], resp.json()['message']
            if status != 'successful':
                message = 'Could not add job [%s]: ' % jobName
                message += ' Scheduler returned error'
                message += ' message: %s' % str(msg)
                sucMsg += message + '\n\n'

        message = {'infoMessage': sucMsg}
        return redirect(url_for('index', messages=json.dumps(message)))

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
