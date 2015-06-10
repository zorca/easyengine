import os
import sys
import random
import shutil
import string
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.shellexec import CommandExecutionError
from ee.core.fileutils import EEFileUtils
from ee.core.git import EEGit
from ee.core.services import EEService
from ee.core.extract import EEExtract
from ee.cli.plugins.mysqlstack import EEMysqlStack
from ee.cli.plugins.nginxstack import EENginxStack
from ee.cli.plugins.phpstack import EEPhpStack
from ee.core.download import EEDownload
from ee.core.mysql import EEMysql
from ee.cli.main import app


class EEAdminStack(EEStack):
    """
        EasyEngine Admin Tools stack
    """
    packages_name = EEVariables.ee_admin
    app = app
    log = app.log

    def __init__(self, package_dict=None, apt_packages=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        package_url : list of urls from where packages to be fetched
        """
        self.apt_packages = apt_packages
        self.manual_packages = package_dict
        self.packages_name = self._get_stack()
        super(EEAdminStack, self).__init__(self.apt_packages)

    def _get_stack(self):
        """
        """
        if self.apt_packages or self.manual_packages:
            if not self.apt_packages:
                return (self.manual_packages)
            elif not self.manual_packages:
                return (self.apt_packages)
            else:
                return (self.apt_packages, self.manual_packages)

        return EEAdminStack.packages_name

    def _set_stack(self):
        """
        """
        
        if type(self.packages_name) is tuple:
            for packages in self.packages_name:
                if type(packages) is list:
                    self.apt_packages = packages
                if type(packages) is dict:
                    self.manual_packages = packages
        elif type(self.packages_name) is dict:
            self.manual_packages = self.packages_name

    def _requirement_check(self):
        """
        Check if requirements for this EEAdminStack stack are fullfilled.
        """
        # Install NGINX stack if not installed
        if not EENginxStack(self).is_installed():
            self.log.info("Installing nginxstack")
            EENginxStack(self).install_stack()

        # Install PHP stack if not installed
        if not EEPhpStack(self).is_installed():
            self.log.info("Installing phpstack")
            EEPhpStack(self).install_stack()

        # Install MySQL stack if not installed
        if not EEMysqlStack(self).is_installed():
            self.log.info("Installing mysqlstack")
            EEMysqlStack(self).install_stack()

    def _install_phpmyadmin(self, file_path):
        """
        """
        print("Installing phpmyadmin, please wait...")
        # Extract phpmyadmin compressed file
        EEExtract.extract(self, file_path, EEVariables.ee_downloads)
        if not os.path.exists('{0}22222/htdocs/db'
                              .format(EEVariables.ee_webroot)):
            self.log.debug("Creating new  directory "
                           "{0}22222/htdocs/db"
                            .format(EEVariables.ee_webroot))
            os.makedirs('{0}22222/htdocs/db'
                        .format(EEVariables.ee_webroot))
        shutil.move('{0}phpmyadmin-STABLE/'.format(EEVariables.ee_downloads),
                    '{0}22222/htdocs/db/pma/'.format(EEVariables.ee_webroot))
        self.log.debug('Setting Privileges of webroot permission to  '
                       '{0}22222/htdocs/db/pma file '.format(EEVariables.ee_webroot))
        EEFileUtils.chown(self, '{0}22222'
                          .format(EEVariables.ee_webroot),
                          EEVariables.ee_php_user,
                          EEVariables.ee_php_user,
                          recursive=True)

    def _install_adminer(self, file_path):
        print("Installing adminer, please wait...")
        shutil.move(file_path,
                    '{0}22222/htdocs/db/'.format(EEVariables.ee_webroot))
        pass

    def _install_wpcli(self, file_path):
        print("Installing wpcli, please wait...")
        shutil.move(file_path, '/usr/bin/wp')

    def _install_phpmemcacheadmin(self, file_path):
        print("Installing phpmemcacheadmin, please wait...")
        if not os.path.exists('{0}22222/htdocs/cache/'
                              .format(EEVariables.ee_webroot)):
            os.makedirs('{0}22222/htdocs/cache/'
                              .format(EEVariables.ee_webroot))
        EEExtract.extract(self, file_path, 
                          '{0}22222/htdocs/cache/memcache'
                          .format(EEVariables.ee_webroot))
        self.log.debug("Setting Privileges to {0}22222/htdocs/cache/memcache file"
                       .format(EEVariables.ee_webroot))
        EEFileUtils.chown(self, '{0}22222'
                         .format(EEVariables.ee_webroot),
                          EEVariables.ee_php_user,
                          EEVariables.ee_php_user,
                          recursive=True)

    def _install_cleancache(self, file_path):
        """
        """
        print("Installing clean php, please wait...")
        shutil.move(file_path, "{0}22222/htdocs/cache/nginx/clean.php"
                    .format(EEVariables.ee_webroot))


    def _install_opcache(self, file_path):
        """
        """
        print("Installing opcache, please wait...")
        pass

    def _install_webgrind(self, file_path):
        print("Installing webgring, please wait...")
        self.log.debug("Extracting file webgrind.tar.gz to "
                       "location /tmp/ ")
        EEExtract.extract(self, file_path, EEVariables.ee_downloads)
        if not os.path.exists('{0}22222/htdocs/php'
                              .format(EEVariables.ee_webroot)):
            self.log.debug("Creating directroy{0}22222/htdocs/php"
                           .format(EEVariables.ee_webroot))
            os.makedirs('{0}22222/htdocs/php'
                        .format(EEVariables.ee_webroot))
        shutil.move('{0}webgrind-master/'.format(EEVariables.ee_downloads),
                    '{0}22222/htdocs/php/webgrind'
                    .format(EEVariables.ee_webroot))

        EEFileUtils.searchreplace(self, "{0}22222/htdocs/php/webgrind/"
                                  "config.php"
                                  .format(EEVariables.ee_webroot),
                                  "/usr/local/bin/dot", "/usr/bin/dot")
        EEFileUtils.searchreplace(self, "{0}22222/htdocs/php/webgrind/"
                                  "config.php"
                                  .format(EEVariables.ee_webroot),
                                  "Europe/Copenhagen",
                                  EEVariables.ee_timezone)

        EEFileUtils.searchreplace(self, "{0}22222/htdocs/php/webgrind/"
                                  "config.php"
                                  .format(EEVariables.ee_webroot),
                                  "90", "100")

        self.log.debug("Setting Privileges of webroot permission to "
                  "{0}22222/htdocs/php/webgrind/ file "
                  .format(EEVariables.ee_webroot))
        EEFileUtils.chown(self, '{0}22222'
                          .format(EEVariables.ee_webroot),
                          EEVariables.ee_php_user,
                          EEVariables.ee_php_user,
                          recursive=True)

    def _install_ptqueryadvisor(self, file_path):
        print("Installing ptqueryadvisor, please wait...")
        shutil.move(file_path, '/usr/bin/pt-query-advisor')
        EEFileUtils.chmod(self, "/usr/bin/pt-query-advisor", 0o775)
        

    def _install_anemometer(self, file_path):
        print("Installing anemometer, please wait...")
        self.log.debug("Extracting file anemometer.tar.gz to "
                          "location /tmp/ ")
        EEExtract.extract(self, file_path, EEVariables.ee_downloads)
        if not os.path.exists('{0}22222/htdocs/db/'
                              .format(EEVariables.ee_webroot)):
            self.log.debug("Creating directory")
            os.makedirs('{0}22222/htdocs/db/'
                        .format(EEVariables.ee_webroot))
        shutil.move('{0}Anemometer-master'.format(EEVariables.ee_downloads),
                    '{0}22222/htdocs/db/anemometer'
                    .format(EEVariables.ee_webroot))
        chars = ''.join(random.sample(string.ascii_letters, 8))
        try:
            EEShellExec.cmd_exec(self, 'mysql < {0}22222/htdocs/db'
                                 '/anemometer/install.sql'
                                 .format(EEVariables.ee_webroot))
        except CommandExecutionError as e:
            raise SiteError("Unable to import Anemometer database")

        EEMysql.execute(self, 'grant select on *.* to \'anemometer\''
                        '@\'{0}\''.format(self.app.config.get('mysql',
                                          'grant-host')))
        self.log.debug("grant all on slow-query-log.*"
                  " to anemometer@root_user IDENTIFIED BY password ")
        EEMysql.execute(self, 'grant all on slow_query_log.* to'
                        '\'anemometer\'@\'{0}\' IDENTIFIED'
                        ' BY \'{1}\''.format(self.app.config.get(
                                             'mysql', 'grant-host'),
                                             chars),
                        errormsg="cannot grant privillages", log=False)

        # Custom Anemometer configuration
        self.log.debug("configration Anemometer")
        data = dict(host=EEVariables.ee_mysql_host, port='3306',
                    user='anemometer', password=chars)
        ee_anemometer = open('{0}22222/htdocs/db/anemometer'
                             '/conf/config.inc.php'
                             .format(EEVariables.ee_webroot),
                             encoding='utf-8', mode='w')
        self.app.render((data), 'anemometer.mustache',
                        out=ee_anemometer)
        ee_anemometer.close()
        pass

    def _remove_phpmyadmin(self):
      """
      """
      EEFileUtils.remove(self, 
                         ['{0}22222/htdocs/db/pma/'
                         .format(EEVariables.ee_webroot)])
      pass

    def _remove_adminer(self):
      """
      """
      EEFileUtils.remove(self, 
                         ['{0}22222/htdocs/db/adminer'
                         .format(EEVariables.ee_webroot)])
      pass

    def _remove_wpcli(self):
      """
      """
      EEFileUtils.remove(self, ['/usr/bin/wp'])
      pass

    def _remove_phpmemcacheadmin(self):
      """
      """
      EEFileUtils.remove(self, 
                         ['{0}22222/htdocs/cache/memcache'
                          .format(EEVariables.ee_webroot)])
      pass

    def _remove_cleancache(self):
      """
      """
      EEFileUtils.remove(self, 
                         ["{0}22222/htdocs/cache/nginx/clean.php"
                         .format(EEVariables.ee_webroot)])
      pass

    def _remove_opcache(self):
      """
      """

      pass

    def _remove_webgrind(self):
      """
      """
      EEFileUtils.remove(self, 
                         ['{0}22222/htdocs/php/webgrind/'
                          .format(EEVariables.ee_webroot)])
      pass

    def _remove_ptqueryadvisor(self):
      """
      """
      EEFileUtils.remove(self, ['/usr/bin/pt-query-advisor'])
      pass

    def _remove_anemometer(self):
      """
      """
      EEFileUtils.remove(self, 
                         ['{0}22222/htdocs/db/anemometer'
                         .format(EEVariables.ee_webroot)])
      pass


    def install_stack(self):
        """
        """
        self._set_stack()
        self._requirement_check()
        self.log.info("Inside Admin Stack")
        #print("Printing final packages %s " %self.packages_name)
        print(".....................Manusl Packages.......................")
        print(self.manual_packages)

        print()
        print("------------------APT Packages-----------------------")
        print(self.apt_packages)
        print("--------------------------------------------------------")
        
        if self.apt_packages:
            super(EEAdminStack, self).install_stack()
        if self.manual_packages:
            for key in self.manual_packages.keys():
                path = EEDownload(('%s' %key), self.manual_packages[key]).download()
                print("Evaluating function %s..." %key)
                print("self._install_{0}(self, '{1}')".format(key, path))
                eval("self._install_{0}('{1}')".format(key, path))

    def remove_stack(self):
      """
      """
      self._set_stack()
      print("Inside Admin Stack")
      print("Printing final packages %s " %self.packages_name)
      print()
      

      print(self.manual_packages)
      
      if self.apt_packages:
          super(EEAdminStack, self).remove_stack()
      if self.manual_packages:
          for key in self.manual_packages.keys():
              print("Evaluating function %s..." %key)
              print("self._remove_{0}(self)".format(key))
              eval("self._remove_{0}()".format(key))


    def purge_stack(self):
      """
      """
      self._set_stack()
      print("Inside Admin Stack")
      # print("Printing final packages %s " %self.packages_name)
      #print()
      

      #print(self.manual_packages)
      
      if self.apt_packages:
          super(EEAdminStack, self).purge_stack()
      if self.manual_packages:
          for key in self.manual_packages.keys():
              print("Evaluating function %s..." %key)
              print("self._remove_{0}(self)".format(key))
              eval("self._remove_{0}()".format(key))
