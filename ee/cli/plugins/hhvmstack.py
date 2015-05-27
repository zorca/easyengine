import os
import sys
from ee.core.variables import EEVariables
from ee.core.aptget import EEAptGet
from ee.core.apt_repo import EERepo
from ee.cli.plugins.eestack import EEStack
from ee.core.shellexec import EEShellExec
from ee.core.services import EEService
from ee.core.shellexec import CommandExecutionError
from ee.core.fileutils import EEFileUtils
from ee.core.git import EEGit
from ee.cli.main import app

class EEHhvmStack(EEStack):
    """
        EasyEngine HHVM stack
    """
    app = app
    log = app.log
    packages_name = EEVariables.ee_hhvm

    def __init__(self, packages_name=None):
        """
        Initialize packages list in stack
        pkgs_name : list of packages to be intialized for operations 
                    in stack
        """

        self.packages_name = self._get_stack()  
        super(EEHhvmStack, self).__init__(self.packages_name)

    def _get_stack(self):
        return EEHhvmStack.packages_name

    def _add_repo(self):
        """
          Add repository for packages to be downloaded from
        """
        self.log.info("Adding HHVM repository, please wait...")
        if (EEVariables.ee_platform_codename == 'precise'):
            self.log.debug(self, 'Adding PPA for Boost')
            EERepo.add(self, ppa=EEVariables.ee_boost_repo)

        self.log.debug(self, 'Adding ppa repo for HHVM')
        EERepo.add(self, repo_url=EEVariables.ee_hhvm_repo)
        self.log.debug(self, 'Adding HHVM GPG Key')
        EERepo.add_key(self, '0x5a16e7281be7a449')
        EEAptGet.update(self)

    def _pre_install_stack(self):
        """
        Defines pre-install activities done before installing hhvm stack
        """
        # Add hhvm repository
        self._add_repo()

    def _post_install_stack(self):
        """
        Defines activities done after installing hhvm stack
        """
        EEShellExec.cmd_exec(self, "update-rc.d hhvm defaults")

        EEFileUtils.searchreplace(self, "/etc/hhvm/server.ini",
                                        "9000", "8000")
        EEFileUtils.searchreplace(self, "/etc/nginx/hhvm.conf",
                                        "9000", "8000")

        with open("/etc/hhvm/php.ini", "a") as hhvm_file:
            hhvm_file.write("hhvm.log.header = true\n"
                            "hhvm.log.natives_stack_trace = true\n"
                            "hhvm.mysql.socket = "
                            "/var/run/mysqld/mysqld.sock\n"
                            "hhvm.pdo_mysql.socket = "
                            "/var/run/mysqld/mysqld.sock\n"
                            "hhvm.mysqli.socket = "
                            "/var/run/mysqld/mysqld.sock\n")

        if os.path.isfile("/etc/nginx/conf.d/fastcgi.conf"):
            if not EEFileUtils.grep(self, "/etc/nginx/conf.d/"
                                    "fastcgi.conf",
                                    "fastcgi_keep_conn"):
                with open("/etc/nginx/conf.d/fastcgi.conf",
                          "a") as hhvm_file:
                    hhvm_file.write("fastcgi_keep_conn on;\n")

        if os.path.isfile("/etc/nginx/conf.d/upstream.conf"):
            if not EEFileUtils.grep(self, "/etc/nginx/conf.d/"
                                    "upstream.conf",
                                    "hhvm"):
                with open("/etc/nginx/conf.d/upstream.conf",
                          "a") as hhvm_file:
                    hhvm_file.write("upstream hhvm {\nserver "
                                    "127.0.0.1:8000;\n"
                                    "server 127.0.0.1:9000 backup;\n}"
                                    "\n")

        EEGit.add(self, ["/etc/hhvm"], msg="Adding HHVM into Git")
        EEService.restart_service(self, 'hhvm')

        if os.path.isfile("/etc/nginx/nginx.conf") and (not
           os.path.isfile("/etc/nginx/common/php-hhvm.conf")):

            data = dict()
            self.log.debug(self, 'Writting the nginx configuration to '
                      'file /etc/nginx/common/php-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/php-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'php-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                      'file /etc/nginx/common/w3tc-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/w3tc-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'w3tc-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                      'file /etc/nginx/common/wpfc-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/wpfc-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpfc-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            self.log.debug(self, 'Writting the nginx configuration to '
                      'file /etc/nginx/common/wpsc-hhvm.conf')
            ee_nginx = open('/etc/nginx/common/wpsc-hhvm.conf',
                            encoding='utf-8', mode='w')
            app.render((data), 'wpsc-hhvm.mustache',
                            out=ee_nginx)
            ee_nginx.close()

            if not EEService.reload_service(self, 'nginx'):
                self.log.error(self, "Failed to reload Nginx, please check "
                                "output of `nginx -t`")


    def install_stack(self):
        """
        Install HHVM stack
        """
        self.log.info("Installing HHVM stack, please wait...")
        self._pre_install_stack()
        super(EEHhvmStack, self).install_stack()
        self._post_install_stack()

    def remove_stack(self):
        """
        Remove HHVM stack
        """
        self.log.info("Removing HHVM stack, please wait...")
        super(EEHhvmStack, self).remove_stack()

    def purge_stack(self):
        self.log.info("Purging HHVM stack, please wait...")
        super(EEHhvmStack, self).purge_stack()
