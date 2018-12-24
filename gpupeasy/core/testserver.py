import requests

# Test one URL at a time
def testURL(url, method='GET', prefix='http://localhost:4004'):
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
                 '/successfuljobs', '/failedjobs']
    postURLList = ['/addnewjob']
    for url in getURList:
        testURL(url)
    for url in postURLList:
        testURL(url, method='POST')

if __name__ =='__main__':
    main()
