import os
import shlex
import re
from flask import Flask, request, session, jsonify

from gpupeasy.core.gpuscheduler import GPUSchedulerCore, Job
from gpupeasy.utils import Logger

class GPUPeasyServer:
    def __init__(self, gpuList, logdir=None, debug=False, wakesec=3):
        '''
        The GPUPeasyServer.
        This server initializes the gpupeasy core scheduler and awaits
        commands. This is a simple flask based server. Security features and
        what not are not implemented.

        gpuList: A list of gpu devices provided as an argument to
            CUDA_VISIBLE_DEVICES environment variable.
            For example, to use gpus 0-2 among 0-3, provide ['0', '1', '2'].
            To use gpus in pairs, provide ['0,1', '2,3'].
            To run on CPU, provide an empty string as an argument.

        logdir: The directory to dump logs. Defaults to '/tmp/gpupeasy/'.
        debug: To run in debug mode.
        wakesec: The wakesec argument for the core scheduler. Defines the
            time in seconds between process status checks and updates.
        '''
        # Should probably have debug levels for the logger: TODO?
        self.__debug = debug
        self.__setupLogging(logdir, debug)
        self.__frontend = Flask('gpupeasy-server')
        self.__backend = GPUSchedulerCore(gpuList, wakesec=wakesec,
                                          logger=self.__logger)
        fe = self.__frontend
        fe.add_url_rule('/deviceutilization', 'getDeviceUtilization',
                        self.__getDeviceUtilization)
        fe.add_url_rule('/scheduledjobs', 'getScheduledJobs',
                        self.__getScheduledJobs)
        fe.add_url_rule('/successfuljobs', 'getSuccessfulJobs',
                        self.__getSuccessfulJobs)
        fe.add_url_rule('/failedjobs', 'getFailedJobs', self.__getFailedJobs)
        fe.add_url_rule('/addnewjob', 'addNewJob', self.__addNewJob,
                        methods=['POST'])
        fe.add_url_rule('/availabledevices', 'getAvailableGPUList',
                        self.__getAvailableGPUList)
        fe.add_url_rule('/jobinfo/<jobID>', 'getJobInfo', self.__getJobInfo)

    def __setupLogging(self, logdir, debug):
        if logdir is None:
            logdir = '/tmp/gpupeasy/'
        if not os.path.exists(logdir):
            # Will fail with exception if something goes wrong. I don't have to
            # handle this as this is a critical error.
            os.mkdirs(logdir)
        # Again, will fail with exception.
        logfile = logdir + '/logs.out'
        logfile = open(logfile, 'a+')
        self.__logger = Logger(fstdout=logfile, fstderr=logfile, debug=debug)

    def __validateJob(self, jobName, jobOutFile, jobCommand):
        '''
        Returns false if error occurred along with error message.
        Else, returns true with None as message
        If user wants to implement custom validator, it should be part of the
        GUI layer and not the core server.
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
            message = 'Output file already exists: %s' % jobOutF
            return False, message
        return True, None

    # URL Handlers
    def __getAvailableGPUList(self):
        '''
        return json:
            {
             'status': 'successful' or 'failed'
             'value' : a list of devices
             }
        '''
        backend = self.__backend
        ret = backend.getAvailableGPUList()
        ret = {'status': 'successful', 'value': ret}
        return jsonify(ret)

    def __getDeviceUtilization(self):
        '''
        returns json:
            {'status': 'successful' or 'failed',
            'value': A list of dict each of the following structure:
                {'jobid': jobid, 'jobName': jobname,
                'jobCommand': jobCommand, 'gpu': gpu}
            }
        '''
        backend = self.__backend
        ret = backend.getRunningJobs()
        jobs = []
        for job in ret:
            command = ' '.join(job.commandList)
            gpu = job.gpu
            jobD = {'jobID': job.jobid, 'jobName': job.name,
                    'jobCommand': command, 'gpu': gpu}
            jobs.append(jobD)
        ret = {'status':'successful', 'value': jobs}
        return jsonify(ret)

    def __getScheduledJobs(self):
        '''
        returns josn:
            {'status': 'successful' or 'failed',
            'value': A list of dict each of the following structure:
                {
                    'jobid': jobid,
                    'jobName': jobname,
                    'jobCommand': jobCommand,
                }
            }
        '''
        backend = self.__backend
        ret = backend.getJobsToSchedule()
        jobs = []
        for job in ret:
            command = ' '.join(job.commandList)
            jobD = {'jobID': job.jobid, 'jobName': job.name,
                    'jobCommand': command}
            jobs.append(jobD)
        ret = {'status':'successful', 'value': jobs}
        return jsonify(ret)

    def __getSuccessfulJobs(self):
        '''
        returns josn:
            {'status': 'successful' or 'failed',
            'value': A list of dict each of the following structure:
                {
                    'jobid': jobid,
                    'jobName': jobname,
                    'jobCommand': jobCommand,
                }
            }
        '''
        backend = self.__backend
        ret = backend.getSucceededJobs()
        jobs = []
        for job in ret:
            command = ' '.join(job.commandList)
            jobD = {'jobID': job.jobid, 'jobName': job.name,
                    'jobCommand': command, 'returnCode': job.returncode}
            jobs.append(jobD)
        ret = {'status':'successful', 'value': jobs}
        return jsonify(ret)

    def __getFailedJobs(self):
        '''
        returns josn:
            {'status': 'successful' or 'failed',
            'value': A list of dict each of the following structure:
                {
                    'jobid': jobid,
                    'jobName': jobname,
                    'jobCommand': jobCommand,
                }
            }
        '''
        backend = self.__backend
        ret = backend.getFailedJobs()
        jobs = []
        for job in ret:
            command = ' '.join(job.commandList)
            jobD = {'jobID': job.jobid, 'jobName': job.name,
                    'jobCommand': command, 'returnCode': job.returncode}
            jobs.append(jobD)
        ret = {'status':'successful', 'value': jobs}
        return jsonify(ret)

    def __getJobInfo(self, jobID):
        '''
        returns json:
            {
                'status': 'successful' or 'failed'
                'value': {
                    'jobid':jobid,
                    'jobname':jobname',
                    'jobCOmmand': 'jobCommand',
                    'outFile' : outFiel,
                    'status': current status

                }
            }
        '''
        ret = self.__backend.getJobInfo(jobID)
        if ret is None:
            msg = {'status': 'failed', 'value': {}}
            return jsonify(msg)
        job = ret
        msg = {'status': 'successful',
               'value': {
                   'jobid': job.jobid,
                   'jobName': job.name,
                   'jobCommand': ' '.join(job.commandList),
                   'outFile': job.stdout.name,
                   'status': job.status,
                   'returnCode' : job.returncode,
               }
              }
        return jsonify(msg)

    def __addNewJob(self):
        '''
        This method is connected to a URL that only accepts POST.
        Further, the post form is assumed to contain the 'job' key. This key
        should index to a dictionary with the following keys:
            1. jobName : String
            2. outFile : String
            3. jobCommand : List parsable by python subprocess module

        Note that it is the callers responsibility to make sure that the
        jobCommand list is parsable by subprocess. No checks are performed by
        the core and the command is passed to subprocess as is.

        Returns a json with key 'status' and value 'failed' or 'successful' and
        an additional key 'message' with an error message.
        '''
        failed = {'status': 'failed'}
        data = request.get_json()
        if data is None:
            failed['message'] = 'No JSON data was found'
            return jsonify(failed)
        if 'job' not in data:
            failed['message'] = 'Key \'job\' not found'
            return jsonify(failed)
        job = data['job']
        keys = ['outFile', 'jobName', 'jobCommand']
        for key in keys:
            if key not in job:
                failed['message'] = 'Key \'%s\' not found' % key
                return jsonify(failed)
        jobName, outFile = job['jobName'], job['outFile']
        jobCommand = job['jobCommand']
        ret, msg = self.__validateJob(jobName, outFile, jobCommand)
        if ret is False:
            failed['message'] = msg
            return jsonify(failed)
        try:
            fp = open(outFile, 'w+')
        except:
            msg = 'Could not open output file: %s' % outFile
            failed['message'] = msg
            return jsonify(failed)

        job = Job(jobName, jobCommand, stdout=fp, stderr=fp)
        ret, jobid = self.__backend.addNewJob(job)
        if ret is False:
            msg = 'Could not add new job: %s. Check logs for details' % jobName
            failed['message'] = msg
            return jsonify(failed)

        success = {'status': 'successful', 'message': 'Job added successfully',
                   'jobID': jobid}
        return jsonify(success)

    def run(self, host, port):
        if not self.__backend.startDaemon():
            return false
        # if user_reloader is set to true, then flask will call initializer
        # twice. This means that two instances of GPUSchedulerCore will be
        # started. (You only run and interact with one though).
        self.__frontend.run(debug=self.__debug, host=host, port=port,
                            use_reloader=False)


if __name__ == '__main__':
    gpu = GPUPeasyServer(['0', '1', '2'], debug=True)
    gpu.run(host='0.0.0.0', port='8888')
