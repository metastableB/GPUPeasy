import sys
import os
import time
import threading
import subprocess
from gpupeasy.utils import Logger, LockedList


class Job:
    def __init__(self, jobname, commandList, stdin=None, stdout=None,
                 stderr=None):
        self.name = jobname
        self.commandList = commandList
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        # This will be set once the process has started
        self.subprocess = None
        self.gpu = None

    def __str__(self):
        return '<' + str(self.jobid) + ', ' + self.name +'>'

    def __repr__(self):
        return '<' + str(self.jobid) + ', ' + self.name +'>'


class GPUSchedulerCore:
    def __init__(self, availableGPU, wakesec=10, maxQueueSize=1000,
                 logger=None):
        '''
        The GPU Scheduler core.

        The core attempts to prove the following functionality:
            1. Maintain queues of commands that re yet to run, have either
            failed or succeeded.
            2. Maintain a status of which command is scheduled on which device.
            3. Allow for adding, deleting, pooling all of these queues.

        availableGPU: is a list of strings which specify the device ID of the
            GPU's to use. For example, ['1', '2', '3'] will schedule
            jobs on GPU 1, 2 and 3. Also, pass [''], to shedule 1 job on CPU,
            ['', ''] to shedule 2 jobs on CPU and so forth. Further, pass
            ['1', '2', '2'] to schedule 1 job on GPU1 and 2 jobs on GPU2.
        wakesec: The number of seconds between checking of completed jobs/free
            GPUs.
            availableGPU cannot be changed once the process has started. TODO

        Note that the public methods, only which should be used to modify
        internals, are not thread-safe.
        '''
        self.__logger = logger
        if logger is None:
            self.__logger = Logger()
        self.__logger.pInfo("Scheduler core initializing")
        self.__availableGPU = LockedList()
        for val in availableGPU:
            self.__availableGPU.append(val)
        assert len(availableGPU) > 0, "Available GPU list is empty"
        # in-case user provides bad value
        self.__wakesec = 10
        self.setWakesec(wakesec)
        self.__maxQueueSize = 1000
        self.setMaxQueueSize(maxQueueSize)
        # If quitFlag is True, the threads will all exit.

        self.__quitFlag = False
        self.__daemonRunning = False
        self.__daemonThr = None
        self.__lastJobId = 1

        self.__toScheduleJobs = LockedList()
        self.__runningJobs = LockedList()
        self.__succeededJobs = LockedList()
        self.__failedJobs = LockedList()
        self.__currAvailableGPUs = LockedList()
        self.__logger.pDebug("Scheduler object: ", self)
        self.__logger.pInfo("Scheduler core initialized")

    def __getNewJobId(self):
        # TODO: Should I bother reusing jobIDs? Or Overflows?
        val = self.__lastJobId
        self.__lastJobId += 1
        return val

    def __updateRunningJobStatus(self):
        # Scan through the list of running jobs. Check if any of them have
        # finished. If they have, move them to finished or succeeded and
        # free-up the GPU.
        idList = []
        runningJobs = self.__runningJobs.getCurrVals()
        for i in range(len(runningJobs)):
            job = runningJobs[i]
            if job.subprocess.poll() is None:
                continue
            rt = job.subprocess.returncode
            if rt != 0:
                self.__logger.pWarn("Process", job,
                                    "exited with return code: %d" % rt)
                self.__failedJobs.append(job)
                idList.append(job.jobid)
            else:
                self.__logger.pSuccess("Process", job,
                                       "exited with return code: %d" % rt)
                self.__succeededJobs.append(job)
            idList.append(job.jobid)
            gpu = job.gpu
            self.__currAvailableGPUs.push(gpu)
            self.__logger.pDebug("Current available gpus",
                                 self.getCurrAvailableGPUs())
        # There is no way to do this safely or cleanly other than using
        # markers. That is, mark objects for deletion and cleanup at different
        # points. I prefer to do this: Slow but cleaner (?).
        for i in range(len(idList)):
            currId = idList[i]
            self.__runningJobs.lock()
            for j in range(len(self.__runningJobs.getCurrVals(unsafe=True))):
                job = self.__runningJobs.getCurrVals(unsafe=True)[j]
                if job.jobid is not currId:
                    continue
                self.__runningJobs.deleteValue(j, unsafe=True)
                gpu = job.gpu
                break
            self.__runningJobs.release()

    def __scheduleNextJob(self):
        '''
        Moves a job from the __toScheduleJobs queue to the __runningJobs queue
        after consuming one gpu device.
        '''
        # There is no conceivable cases in which this should happen; if I'm
        # being careful. SchduleNextJob should only be called after a gpu is
        # made available.
        msg = "Internal error"
        assert len(self.__currAvailableGPUs) > 0, self.__logger.pCritial(msg)
        gpu = self.__currAvailableGPUs.pop()
        job = self.__toScheduleJobs.pop()
        assert job.subprocess == None, self.__logger.pCritial(msg)
        self.__logger.pInfo("Scheduling", job, "on gpu ", gpu)
        # Handling subprocesses
        # https://stackoverflow.com/questions/16071866/non-blocking-subprocess-call
        # https://docs.python.org/2/library/subprocess.html#subprocess.Popen
        # TODO: Make the argument passing task a little easier. By this point,
        # i'm assuming the commandlist is valid
        try:
            env = os.environ.copy()
            env["CUDA_VISIBLE_DEVICES"] = gpu
            subpro = subprocess.Popen(job.commandList, stdin=job.stdin,
                                      stdout=job.stdout, stderr=job.stderr,
                                      env=env)
            job.subprocess = subpro
            job.gpu = gpu
            self.__runningJobs.append(job)
            return
        except OSError as e:
            self.__logger.pError("Scheduling failed for", job, "on gpu", gpu)
            self.__logger.pError("OSError: ", str(e))
        except ValueError as e:
            self.__logger.pError("Scheduling failed for", job, "on gpu", gpu)
            self.__logger.pError("ValueError:", str(e))
        self.__failedJobs.append(job)
        self.__currAvailableGPUs.push(gpu)

    def __daemonThread(self):
        # There is no conceivable cases in which this error should happen.
        msg = "Internal error"
        assert self.__daemonRunning == False, self.__logger.pCritical(msg)
        assert len(self.__runningJobs) == 0, self.__logger.pCritial(msg)
        assert len(self.__toScheduleJobs) == 0, self.__logger.pCritial(msg)
        assert len(self.__succeededJobs) == 0, self.__logger.pCritial(msg)
        assert len(self.__failedJobs) == 0, self.__logger.pCritial(msg)
        assert len(self.__currAvailableGPUs) == 0, self.__logger.pCritial(msg)
        assert self.__daemonRunning == False, self.__logger.pCritial(msg)
        self.__daemonRunning = True
        tmp = self.__availableGPU.getCurrVals()
        for val in tmp:
            self.__currAvailableGPUs.append(val)
        while self.__quitFlag is False:
            self.__updateRunningJobStatus()
            sleep = (len(self.__currAvailableGPUs) == 0)
            sleep = sleep or (len(self.__toScheduleJobs) == 0)
            if sleep:
                time.sleep(self.__wakesec)
                continue
            # At this point, GPUs are free.
            if len(self.__toScheduleJobs) == 0:
                continue
            self.__scheduleNextJob()
        self.__logger.pInfo('Exiting daemon')
        self.__daemonRunning = False

    def addNewJob(self, job):
        if not self.__daemonRunning:
            self.__logger.pWarn('Add job attempted while daemon not running')
            return False, None
        # check if we can add a new job
        if len(self.__toScheduleJobs) >= self.__maxQueueSize:
            self.__logger.pError("Adding new job failed. Queue full.")
            return False, None
        job.jobid = self.__getNewJobId()
        self.__toScheduleJobs.append(job)
        return True, job.jobid

    def setAvailabelGPU(self, availableGPU):
        raise NotImplementedError

    def setWakesec(self, wakesec):
        try:
            wakesec = int(wakesec)
        except:
            self.__logger.pError("wakesec not updated. Invalid value for " +
                                   "wakesec. Should be positive Integer")
            return
        if wakesec <= 0:
            self.__logger.pError("wakesec not updated. Invalid value for " +
                                   "wakesec. Should be positive Integer")
            return
        self.__wakesec = wakesec
        self.__logger.pInfo("Wakesec updated to: %d" % wakesec)

    def setMaxQueueSize(self, maxQueueSize):
        try:
            maxQueueSize = int(maxQueueSize)
        except:
            self.__logger.pError("maxQueueSize not updated. Invalid value for " +
                                   "maxQueueSize. Should be positive Integer")
            return
        if maxQueueSize <= 0:
            self.__logger.pError("maxQueueSize not updated. Invalid value for " +
                                   "maxQueueSize. Should be positive Integer")
            return
        self.__maxQueueSize = maxQueueSize
        self.__logger.pInfo("maxQueueSize updated to: %d" % maxQueueSize)

    def getAvailableGPUList(self):
        val = self.__availableGPU.getCurrVals()
        return val

    def getCurrAvailableGPUs(self):
        val = self.__availableGPU.getCurrVals()
        return val

    def getWakesec(self):
        return self.__wakesec

    def getJobsToSchedule(self):
        val = self.__toScheduleJobs.getCurrVals()
        return val

    def getRunningJobs(self):
        val = self.__runningJobs.getCurrVals()
        return val

    def getSucceededJobs(self):
        val = self.__succeededJobs.getCurrVals()
        return val

    def getFailedJobs(self):
        val = self.__failedJobs.getCurrVals()
        return val

    def stopDaemon(self):
        self.__quitFlag = True
        self.__logger.pInfo('Stop received')
        while (self.__daemonRunning is True) and (self.__daemonThr.isAlive()):
            time.sleep(0.05)
        self.__logger.pInfo('Daemon exited')
        return

    def startDaemon(self):
        '''
        Note that start daemon is non blocking and does not call join on the
        daemon thread. That is, if the caller thread dies, so does the daemon
        thread. This is by design.

        Returns True on success and false on failure. Check logs for details.
        '''
        if self.__daemonRunning is True:
            self.__logger.pError('Daemon already running')
            return False
        self.__daemonThr = threading.Thread(target=self.__daemonThread,
                                            name='scheduler-daemon')
        self.__logger.pInfo("Starting up")
        self.__daemonThr.start()
        while self.__daemonRunning is False:
            time.sleep(0.05)
        self.__logger.pInfo("Daemon started")
        return True


def main():
    # Start the gpu-scheduler daemon
    logger = Logger()
    gpus = GPUSchedulerCore(['0', '1'], wakesec=1, logger=logger)
    gpus.startDaemon()
    time.sleep(3)
    def printQZ():
        logger.pDebug('Running: ', gpus.getRunningJobs())
        logger.pDebug('To Schedule: ', gpus.getJobsToSchedule())
        logger.pDebug('Succeded: ', gpus.getSucceededJobs())
        logger.pDebug('Failed:   ', gpus.getFailedJobs())

    # Add first command
    job = Job('ls00', ['ls', '-l'])
    devnull = open('/tmp/gpus', 'w+')
    job.stderr = devnull
    job.stdout = devnull
    gpus.addNewJob(job)
    time.sleep(4)
    printQZ()

    time.sleep(2)
    job = Job('exited', ['./test.sh', '10'])
    gpus.addNewJob(job)
    printQZ()

    time.sleep(2)
    job = Job('sleep5', ['sleep', '5'])
    gpus.addNewJob(job)
    printQZ()

    time.sleep(2)
    job = Job('sleep10', ['sleep', '10'])
    gpus.addNewJob(job)
    printQZ()

    time.sleep(2)
    job = Job('doomed', ['doom', '10'])
    gpus.addNewJob(job)
    printQZ()

    time.sleep(2)
    job = Job('doomed2', ['./test2.sh', '10'])
    gpus.addNewJob(job)
    printQZ()

    time.sleep(2)
    job = Job('sleep15', ['sleep', '15'])
    gpus.addNewJob(job)
    printQZ()

    time.sleep(2)
    job = Job('sleep20', ['sleep', '20'])
    gpus.addNewJob(job)
    printQZ()
    i = 0

    while i < 10:
        printQZ()
        time.sleep(4); i += 1
    gpus.stopDaemon()


if __name__ == '__main__':
    main()
