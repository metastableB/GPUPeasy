import requests
import time

def testAddJobs(url, method='GET', prefix='http://localhost:8888'):
    url = prefix + url

    jobs = [
        {'job':{'jobName': 'ls0', 'outFile': '/tmp/ls/00',
                   'jobCommand':['sleep','200']}},
        {'job':{'jobName': 'fail00', 'outFile': '/tmp/ls/20',
                   'jobCommand':['seep','1200']}},
        {'job':{'jobName': 'fail01', 'outFile': '/tmp/ls/21',
                   'jobCommand':['seep','1200']}},
        {'job':{'jobName': 'ls1', 'outFile': '/tmp/ls/01',
                   'jobCommand':['sleep','1200']}},
        {'job':{'jobName': 'ls2', 'outFile': '/tmp/ls/02',
                   'jobCommand':['sleep','400']}},
        {'job':{'jobName': 'ls3', 'outFile': '/tmp/ls/03',
                   'jobCommand':['sleep','200']}},
        {'job':{'jobName': 'ls4', 'outFile': '/tmp/ls/04',
                   'jobCommand':['sleep','1200']}},
        {'job':{'jobName': 'ls5', 'outFile': '/tmp/ls/05',
                   'jobCommand':['sleep','400']}},
    ]

    for job in jobs:
        r = requests.post(url, json=job)
        assert r.status_code == 200, r.status_code
        print(r.json())

# Test one URL at a time
def testURL(url, method='GET', prefix='http://localhost:8888'):
    url = prefix + url
    if method == 'GET':
        r = requests.get(url)
        assert r.status_code == 200, r.status_code
        print(r.json())

    if method == 'POST':
        r = requests.post(url)
        assert r.status_code == 200, r.status_code
        print(r.json())


def main():
    getURList = ['/deviceutilization', '/scheduledjobs',
                 '/successfuljobs', '/failedjobs', '/availabledevices']
    postURLList = ['/addnewjob']
    for url in getURList:
        print('URL:', url)
        testURL(url)
        print()
    for url in postURLList:
        print('URL:', url)
        testURL(url, method='POST')
        print()

    testAddJobs('/addnewjob', method='POST')
    time.sleep(5)
    getURList = ['/jobinfo/1', '/jobinfo/2', '/jobinfo/3']
    for url in getURList:
        testURL(url)

if __name__ =='__main__':
    main()
