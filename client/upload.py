import argparse
import os.path

import requests


# flake8: noqa
class FileUpload:

    def do(self, args):
        package_id = args.package_id

        if args.package:
            package = self.upload_package(args)
            package_id = package["package_id"]
        if args.symbol:
            self.upload_symbol(args, package_id)

    def do_upload(self, token, file, upload_type, upload_url):
        with open(file, 'rb') as f:
            if upload_type == 'AlibabaCloudOSS':
                r = requests.put(upload_url, data=f)
                r.raise_for_status()
            elif upload_type == 'AmazonAWSS3':
                files = {'file': (file, f)}
                r = requests.post(upload_url, data=r.json()['fields'], files=files)
                r.raise_for_status()
            elif upload_type == 'LocalFileSystem':
                headers = {
                    'Authorization': 'Token ' + token
                }
                data = {"file": f}
                r = requests.post(upload_url, files=data, headers=headers)
                print(r.json())
            else:
                print("unknown upload type " + upload_type)
                raise
        return r

    def upload_package(self, args):
        request_upload_url = os.path.join(args.api_url, 'upload/package/request')
        payload = {
            'filename': os.path.basename(args.package),
        }
        if args.commit_id:
            payload['commit_id'] = args.commit_id
        if args.build_type:
            payload['build_type'] = args.build_type
        if args.channel:
            payload['channel'] = args.channel
        if args.description:
            payload['description'] = args.description
        # try:
        #     cmd = "git log -15 --oneline --format=%s | sed 's/^.*: //' | grep -v ^Merge | grep -v ^accepted | head -n 5"
        #     description = subprocess.check_output(cmd, shell=True, encoding='UTF-8')
        #     payload['description'] = description
        # except:
        #     pass

        headers = {
            'Authorization': 'Token ' + args.token
        }
        r = requests.post(request_upload_url, data=payload, headers=headers)
        print(r.json())
        upload_type = r.json()['storage']
        upload_url = r.json().get('upload_url', '')
        record_id = r.json().get('record_id', '')
        r = self.do_upload(args.token, args.package, upload_type, upload_url)

        if upload_type == 'LocalFileSystem':
            return r.json()

        url = os.path.join(args.api_url, 'upload/package/record/' + str(record_id))
        r = requests.put(url, headers=headers)
        print(r.status_code)
        print(r.json())
        return r.json()['data']

    def upload_symbol(self, args, package_id):
        request_upload_url = os.path.join(args.api_url, 'upload/symbol/request/' + str(package_id))
        payload = {
            'filename': os.path.basename(args.symbol),
        }
        headers = {
            'Authorization': 'Token ' + args.token
        }
        r = requests.post(request_upload_url, data=payload, headers=headers)
        print(r.json())
        upload_type = r.json()['storage']
        upload_url = r.json().get('upload_url', '')
        record_id = r.json().get('record_id', '')
        r = self.do_upload(args.token, args.symbol, upload_type, upload_url)

        if upload_type == 'LocalFileSystem':
            return r.json()
        url = os.path.join(args.api_url, 'upload/symbol/record/' + str(record_id))
        r = requests.put(url, headers=headers)
        print(r.json())
        return r.json()['data']


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--api_url', required=True, help='api base url')
    parser.add_argument('--token', required=True, help='the application upload token')
    parser.add_argument('--package', help='package file path')
    parser.add_argument('--symbol', help='symbol file path')
    parser.add_argument('--description', help='description')
    parser.add_argument('--commit_id', help='commit id')
    parser.add_argument('--build_type', help='build type')
    parser.add_argument('--channel', help='build channel')
    parser.add_argument('--package_id', help='package id')

    args = parser.parse_args()
    print(args)
    upload = FileUpload()
    upload.do(args)


if __name__ == "__main__":
    main()
