"""EasyEngine download core classes."""
import urllib.request
import urllib.error
import os
from ee.core.logging import Log
from ee.core.variables import EEVariables
from ee.cli.main import app


class EEDownload():
    """Method to download using urllib"""
    app = app
    log = app.log
    def __init__(self, package, url, out_file=None, out_path=None):
        """
        Download packages
        package : string, name of package to be downloaded
        url : string, url of the package to be downloaded from
        out_file : filename the package to be downloaded to
        out_path : directory name the package to be downloaded to.
        """
        self.package = package
        self.url = url
        self.out_file = out_file
        self.out_path = out_path
        self.default_path = EEVariables.ee_downloads

        pass

    def download(self):
        """
        Download packages
        """
       
        try:
            if not self.out_path:
                self.out_path = self.default_path

            directory = os.path.dirname(self.out_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

            if not self.out_file:
                self.out_file = self.url.split('/')[-1]
                

            outfilepath = self.out_path + self.out_file
            # directory = os.path.dirname(filename) 
            # if not os.path.exists(directory):
            #     os.makedirs(directory)
            print(self.package)
            self.log.info("Downloading {0}, please wait...".format(self.package))
            urllib.request.urlretrieve(self.url, outfilepath)
            return outfilepath
    
        except urllib.error.URLError as e:
            self.log.debug("[{err}]".format(err=str(e.reason)))
            self.log.error("Package download failed. {0}"
                           .format(self.package)) 
            return False
        except urllib.error.HTTPError as e:
            self.log.error("Package download failed. {0}"
                           .format(self.package))
            self.log.debug("[{err}]".format(err=str(e.reason)))
            return False
        except urllib.error.ContentTooShortError as e:
            self.log.debug("{0}{1}".format(e.errno, e.strerror))
            self.log.error("Package download failed. The amount of the"
                           " downloaded data is less than "
                           "the expected amount \{0} ".format(self.package))
            return False
