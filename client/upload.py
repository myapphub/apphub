import os.path
import subprocess
import sys

import requests


# flake8: noqa
class FileUpload:

    def __init__(self, argv):
        self.api_url = argv[1]
        if not self.api_url.endswith('/'):
            self.api_url += '/'
        self.token = argv[2]
        self.file = argv[3]
        self.type = argv[4]
        self.argv = argv

    def do_upload(self, upload_type, upload_url):
        with open(self.file, 'rb') as f:
            if upload_type == 'AlibabaCloudOSS':
                r = requests.put(upload_url, data=f)
                r.raise_for_status()
            elif upload_type == 'AmazonAWSS3':
                files = {'file': (self.file, f)}
                r = requests.post(upload_url, data=r.json()['fields'], files=files)
                r.raise_for_status()
            elif upload_type == 'LocalFileSystem':
                headers = {
                    'Authorization': 'Token ' + self.token
                }
                data = {"file": f}
                r = requests.post(upload_url, files=data, headers=headers)
                print(r.json())
            else:
                print("unknown upload type " + upload_type)
                raise
        return r

    def upload_package(self):
        argv = self.argv
        request_upload_url = os.path.join(self.api_url, 'upload/package/request')
        payload = {
            'filename': os.path.basename(self.file),
        }
        payload['commit_id'] = argv[5]
        payload['build_type'] = argv[6]
        try:
            cmd = "git log -15 --oneline --format=%s | sed 's/^.*: //' | grep -v ^Merge | grep -v ^accepted | head -n 5"
            description = subprocess.check_output(cmd, shell=True, encoding='UTF-8')
            payload['description'] = description
        except:
            pass

        headers = {
            'Authorization': 'Token ' + self.token
        }
        r = requests.post(request_upload_url, data=payload, headers=headers)
        print(r.json())
        upload_type = r.json()['storage']
        upload_url = r.json().get('upload_url', '')
        record_id = r.json().get('record_id', '')
        r = self.do_upload(upload_type, upload_url)

        if upload_type == 'LocalFileSystem':
            return r.json()

        url = os.path.join(self.api_url, 'upload/package/record/' + str(record_id))
        r = requests.put(url, headers=headers)
        print(r.json())
        return r.json()['data']

    def upload_symbol(self):
        package_id = self.argv[5]
        request_upload_url = os.path.join(self.api_url, 'upload/symbol/request/' + str(package_id))
        payload = {
            'filename': os.path.basename(self.file),
        }
        headers = {
            'Authorization': 'Token ' + self.token
        }
        r = requests.post(request_upload_url, data=payload, headers=headers)
        print(r.json())
        upload_type = r.json()['storage']
        upload_url = r.json().get('upload_url', '')
        record_id = r.json().get('record_id', '')
        r = self.do_upload(upload_type, upload_url)

        if upload_type == 'LocalFileSystem':
            return r.json()
        url = os.path.join(self.api_url, 'upload/symbol/record/' + str(record_id))
        r = requests.put(url, headers=headers)
        print(r.json())
        return r.json()['data']


def main():
    upload = FileUpload(sys.argv)
    if upload.type == "package":
        upload.upload_package()
    elif upload.type == "symbol":
        upload.upload_symbol()


if __name__ == "__main__":
    main()
