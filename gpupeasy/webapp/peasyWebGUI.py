import os
import json
import shlex
import re
from flask import Flask, flash, redirect, jsonify, url_for
from flask import render_template, request, session, abort
import requests
import subprocess

from gpupeasy.core.server import GPUPeasyServer


class GPUPeasyWebGUI:
    def __init__(self, coreHost, corePort, debug=False):
        self.__frontend = Flask(__name__)
        self.__cHost = coreHost
        self.__cPort = corePort
        self.__debug = debug

        # Used to sync with backend for lazy updates.
        # That is, data is sent to the web-gui iff the internal statelist
        # and backends list differs, indicating and update.
        self.__successList = []
        self.__failedList = []
        self.__scheduledList = []

        fe = self.__frontend
        fe.add_url_rule('/message', 'messageTest',
                        self.__messageTest)
        fe.add_url_rule('/', 'index', self.__index)
        fe.add_url_rule('/deviceutilization', 'getDeviceUtilization',
                        self.__getDeviceUtilization)
        fe.add_url_rule('/batchaddjobs', 'batchAddJobs', self.__batchAddJobs,
                        methods=['GET', 'POST'])
        fe.add_url_rule('/jobinfo/<jobID>', 'getJobInfo', self.__getJobInfo)
        fe.add_url_rule('/testCommandParser', 'testCommandParser',
                        self.__testCommandParser, methods=['POST'])
        fe.add_url_rule('/successfuljobs', 'getSuccessfulJobs',
                        self.__getSuccessfulJobs)
        fe.add_url_rule('/failedjobs', 'getFailedJobs',
                        self.__getFailedJobs)
        fe.add_url_rule('/scheduledjobs', 'getScheduledJobs',
                        self.__getScheduledJobs)
        fe.add_url_rule('/loadlogfile', 'loadLogFile',
                        self.__loadLogFile, methods=['POST'])

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

    def __cleanJobListString(self, string):
        jobList = string.strip()
        jobList = jobList.replace('\n', ' ').replace('\r', ' ')
        jobList = re.sub(' +', ' ', jobList)
        return jobList

    def __parseCommand(self, commandString):
        jobCommand = shlex.split(commandString)
        jobCommand = [x.strip() for x in jobCommand]
        return jobCommand

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
            value = value.replace('\n', '<br \>')
            msg[key] = value
        return render_template('index.html', **msg)

    def __testCommandParser(self):
        jobCommand = request.form['jobCommand']
        if len(jobCommand) == 0:
            ret = {
                'status': 'failed', 'commandList': [],
                'errorMessage': 'Command string cannot be emtpy'
            }
            ret = json.dumps(ret)
            return redirect(url_for('batchAddJobs', messages=ret))

        jobCommand = self.__cleanJobListString(jobCommand)
        ret = self.__parseCommand(jobCommand)
        ret = [x.strip() for x in ret]
        ret = {
            'status': 'successful',
            'commandList': ret,
        }
        ret = json.dumps(ret)
        return redirect(url_for('batchAddJobs', messages=ret))

    def __batchAddJobs(self):
        if request.method == 'GET':
            if 'messages' not in request.args:
                return render_template('addjobs.html')

            msg = json.loads(request.args['messages'])
            return render_template('addjobs.html', **msg)

        jobList = request.form['jobList']
        jobList = self.__cleanJobListString(jobList)
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
        sucMsg = 'Jobs successfully passed onto scheduler.\n'
        for job in jobList:
            jobS = job.split(';;')
            jobS = [x.strip() for x in jobS]
            jobS = [x for x in jobS if len(x) > 0]
            jobName, jobOutF, jobCommand = jobS[0], jobS[1], jobS[2]
            jobCommand = self.__parseCommand(jobCommand)
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

    def __getJobInfo(self, jobID):
        url = 'http://%s:%s/jobinfo/%d' % (self.__cHost, self.__cPort,
                                           int(jobID))
        jobInfo, msg = self.__makeCoreRequest(url, method='GET')
        if jobInfo is None:
            msg = 'None %s' %  msg
            return render_template('jobinfo.html', errorMessage=msg)
        js = jobInfo.json()
        if js['status'] != 'successful':
            msg = 'Job (%s) not found in backend (TODO CHANGE THIS)' % jobID
            return render_template('jobinfo.html', errorMessage=msg)
        jobInfo = js['value']
        return render_template('jobinfo.html', **jobInfo)

    def __loadLogFile(self):
        '''
        Only accepts POST
        filename, last N. N can be negative to read from start.
        '''
        filename = request.form['fileName']
        N = request.form['lastN']
        N = int(N)
        ret = {'status': 'failed', 'value': ''}
        if not os.path.exists(filename):
            msg = 'File not found: %s' % filename
            ret['value'] = msg
            return jsonify(msg)
        f = subprocess.Popen(['tail','-n', '%d' % N, filename],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        f.wait()
        if f.returncode != 0:
            msg = 'Could not read file: %s\n' % (filename)
            msg += 'tail returned error code %d' % (f.returncode)
            ret['value'] = msg
            return jsonify(ret)
        lines = f.stdout.readlines()
        lines = [x.decode('utf-8') for x in lines]
        lines = ''.join(lines)
        ret['status'] = 'successful'
        ret['value'] = lines
        return jsonify(ret)

    def __getSuccessfulJobs(self):
        '''
        TODO:
        Maintain an internal list. Fetch from backend. Only send data if the
        internal state differs from backend
        '''
        url = 'http://%s:%s/successfuljobs' % (self.__cHost, self.__cPort)
        successfulJobs, msg = self.__makeCoreRequest(url, method='GET')
        if successfulJobs is None:
            return render_template('queue.html', errorMessage=msg)
        ret = successfulJobs.json()
        if ret['status'] != 'successful':
            msg = 'Error: GPUPeasy scheduler server returned an error'
            return render_template('queue.html', errorMessage=msg)
        ret = ret['value']
        if len(ret) == 0:
            emptyMessage="No successful jobs"
            return render_template('queue.html', emptyMessage=emptyMessage)
        return render_template('queue.html', jobs=ret)

    def __getFailedJobs(self):
        '''
        TODO:
        Maintain an internal list. Fetch from backend. Only send data if the
        internal state differs from backend
        '''
        url = 'http://%s:%s/failedjobs' % (self.__cHost, self.__cPort)
        failedJobs, msg = self.__makeCoreRequest(url, method='GET')
        if failedJobs is None:
            return render_template('queue.html', errorMessage=msg)
        ret = failedJobs.json()
        if ret['status'] != 'successful':
            msg = 'Error: GPUPeasy scheduler server returned an error'
            return render_template('queue.html', errorMessage=msg)
        ret = ret['value']
        if len(ret) == 0:
            emptyMessage="No jobs have failed"
            return render_template('queue.html', emptyMessage=emptyMessage)
        return render_template('queue.html', jobs=ret)

    def __getScheduledJobs(self):
        '''
        TODO:
        Maintain an internal list. Fetch from backend. Only send data if the
        internal state differs from backend
        '''
        url = 'http://%s:%s/scheduledjobs' % (self.__cHost, self.__cPort)
        scheduledjobs, msg = self.__makeCoreRequest(url, method='GET')
        if scheduledjobs is None:
            return render_template('queue.html', errorMessage=msg)
        ret = scheduledjobs.json()
        if ret['status'] != 'successful':
            msg = 'Error: GPUPeasy scheduler server returned an error'
            return render_template('queue.html', errorMessage=msg)
        ret = ret['value']
        if len(ret) == 0:
            emptyMessage="No jobs scheduled"
            return render_template('queue.html', emptyMessage=emptyMessage)
        return render_template('queue.html', jobs=ret)

    def run(self, host, port):
        self.__frontend.run(debug=self.__debug, host=host, port=port)




if __name__ == "__main__":
    frontend = GPUPeasyWebGUIchedulerGUi('localhost', '8888', debug=True)
    frontend.run(host='0.0.0.0', port='4004')
