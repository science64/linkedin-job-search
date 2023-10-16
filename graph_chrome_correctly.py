import requests
import os
import re
import zipfile
import wget

class download_chromedriver():
    def __init__(self):


        if os.name == 'nt':
            replies = os.popen(r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version').read()
            replies = replies.split('\n')
            print(replies)
            for reply in replies:
                if 'version' in reply:
                    reply = reply.rstrip()
                    reply = reply.lstrip()
                    print(reply)
                    if '.' in reply:
                        self.version_number = reply.split('REG_SZ')[1].strip()
                        break

    def download(self):

        self.download_url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{self.version_number}/win64/chrome-win64.zip"
        print(self.download_url)
        # download the zip file using the url built above
        latest_driver_zip = wget.download(self.download_url, out='./files/chromedriver.zip')

        # extract the zip file
        with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
            zip_ref.extractall(path = './files/') # you can specify the destination folder path here
        # delete the zip file downloaded above
        os.remove(latest_driver_zip)
        # os.rename(driver_binaryname, target_name)
        # os.chmod(target_name, 755)
