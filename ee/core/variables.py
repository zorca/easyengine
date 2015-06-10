"""EasyEngine core variable module"""
import platform
import socket
import configparser
import os
import sys
import psutil
import datetime


class EEVariables():
    """Intialization of core variables"""

    # EasyEngine version
    ee_version = "3.1.9"

    ee_downloads = "/tmp/ee/downloads/"

    # EasyEngine packages versions
    ee_wp_cli = "0.19.1"
    ee_adminer = "4.2.1"
    ee_roundcube = "1.1.1"
    ee_vimbadmin = "3.0.11"

    # Current date and time of System
    ee_date = datetime.datetime.now().strftime('%d%b%Y%H%M%S')

    # EasyEngine core variables
    ee_platform_distro = platform.linux_distribution()[0].lower()
    ee_platform_version = platform.linux_distribution()[1]
    ee_platform_codename = os.popen("lsb_release -sc | tr -d \'\\n\'").read()

    # Get timezone of system
    if os.path.isfile('/etc/timezone'):
        with open("/etc/timezone", "r") as tzfile:
            ee_timezone = tzfile.read().replace('\n', '')
            if ee_timezone == "Etc/UTC":
                ee_timezone = "UTC"
    else:
        ee_timezone = "UTC"

    # Get FQDN of system
    ee_fqdn = socket.getfqdn()

    # EasyEngien default webroot path
    ee_webroot = '/var/www/'

    # PHP5 user
    ee_php_user = 'www-data'

    # Get git user name and EMail
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~")+'/.gitconfig')
    try:
        ee_user = config['user']['name']
        ee_email = config['user']['email']
    except Exception as e:
        ee_user = input("Enter your name: ")
        ee_email = input("Enter your email: ")
        os.system("git config --global user.name {0}".format(ee_user))
        os.system("git config --global user.email {0}".format(ee_email))

    # Get System RAM and SWAP details
    ee_ram = psutil.virtual_memory().total / (1024 * 1024)
    ee_swap = psutil.swap_memory().total / (1024 * 1024)

    # MySQL hostname
    ee_mysql_host = ""
    config = configparser.RawConfigParser()
    cnfpath = os.path.expanduser("~")+"/.my.cnf"
    if [cnfpath] == config.read(cnfpath):
        try:
            ee_mysql_host = config.get('client', 'host')
        except configparser.NoOptionError as e:
            ee_mysql_host = "localhost"
    else:
        ee_mysql_host = "localhost"

    # EasyEngine stack installation varibales
    # Nginx repo and packages
    if ee_platform_distro == 'ubuntu':
        ee_nginx_repo = "ppa:rtcamp/nginx"
        ee_nginx = ["nginx-custom", "nginx-common"]
    elif ee_platform_distro == 'debian':
        ee_nginx_repo = ("deb http://packages.dotdeb.org {codename} all"
                         .format(codename=ee_platform_codename))
        ee_nginx = ["nginx-extras", "nginx-common"]

    # PHP repo and packages
    if ee_platform_distro == 'ubuntu':
        ee_php_repo = "ppa:ondrej/php5-5.6"
    elif ee_platform_codename == 'wheezy':
        ee_php_repo = ("deb http://packages.dotdeb.org {codename}-php56 all"
                       .format(codename=ee_platform_codename))
    ee_php = ["php5-fpm", "php5-curl", "php5-gd", "php5-imap",
              "php5-mcrypt", "php5-common", "php5-readline",
              "php5-mysql", "php5-cli", "php5-memcache", "php5-imagick",
              "memcached", "graphviz", "php-pear"]

    if ee_platform_codename == 'wheezy':
        ee_php = ee_php + ["php5-dev"]

    if ee_platform_distro == 'ubuntu' or ee_platform_codename == 'jessie':
        ee_php = ee_php + ["php5-xdebug"]

    # MySQL repo and packages
    if ee_platform_distro == 'ubuntu':
        ee_mysql_repo = ("deb http://mirror.aarnet.edu.au/pub/MariaDB/repo/"
                         "10.0/ubuntu {codename} main"
                         .format(codename=ee_platform_codename))
    elif ee_platform_distro == 'debian':
        ee_mysql_repo = ("deb http://mirror.aarnet.edu.au/pub/MariaDB/repo/"
                         "10.0/debian {codename} main"
                         .format(codename=ee_platform_codename))

    ee_mysql = ["mariadb-server", "percona-toolkit"]

    # Postfix repo and packages
    ee_postfix_repo = ""
    ee_postfix = ["postfix"]

    # Mail repo and packages
    ee_mail_repo = ("deb http://http.debian.net/debian-backports {codename}"
                    "-backports main".format(codename=ee_platform_codename))

    ee_mail = ["dovecot-core", "dovecot-imapd", "dovecot-pop3d",
               "dovecot-lmtpd", "dovecot-mysql", "dovecot-sieve",
               "dovecot-managesieved", "postfix-mysql", "php5-cgi",
               "php-gettext", "php-pear"]

    # Mailscanner repo and packages
    ee_mailscanner_repo = ()
    ee_mailscanner = ["amavisd-new", "spamassassin", "clamav", "clamav-daemon",
                      "arj", "zoo", "nomarch", "lzop", "cabextract", "p7zip",
                      "rpm", "unrar-free"]

    # HHVM repo details
    # 12.04 requires boot repository
    if ee_platform_distro == 'ubuntu':
        if ee_platform_codename == "precise":
            ee_boost_repo = ("ppa:mapnik/boost")

        ee_hhvm_repo = ("deb http://dl.hhvm.com/ubuntu {codename} main"
                        .format(codename=ee_platform_codename))
    else:
        ee_hhvm_repo = ("deb http://dl.hhvm.com/debian {codename} main"
                        .format(codename=ee_platform_codename))

    ee_hhvm = ["hhvm"]

    ee_wpclistack = {
                      'wpcli': "https://github.com/wp-cli/wp-cli/releases/download/"
                               "v{0}/wp-cli-{0}.phar".format(ee_wp_cli)
    }

    ee_phpmyadminstack = {
                           'phpmyadmin': "https://github.com/phpmyadmin/phpmyadmin/archive/STABLE.tar.gz", 
                         }

    ee_adminerstack = {
                        'adminer': "http://downloads.sourceforge.net/adminer/adminer-{0}.php".format(ee_adminer),
                      }

    ee_admin = {
                'phpmyadmin': "https://github.com/phpmyadmin/phpmyadmin/archive/STABLE.tar.gz",
                'adminer': "http://downloads.sourceforge.net/adminer/adminer-{0}.php".format(ee_adminer),
                'phpmemcacheadmin' : "http://phpmemcacheadmin.googlecode.com/files/phpMemcachedAdmin-1.2.2-r262.tar.gz",
                'cleancache' : "https://raw.githubusercontent.com/rtCamp/eeadmin/master/cache/nginx/clean.php",
                'opcache' : "https://raw.github.com/rlerdorf/opcache-status/master/opcache.php",
                'webgrind' : "https://github.com/jokkedk/webgrind/archive/master.tar.gz",
                'ptqueryadvisor' : "http://bazaar.launchpad.net/~percona-toolkit-dev/percona-toolkit/2.1/download/head:/ptquerydigest-20110624220137-or26tn4expb9ul2a-16/pt-query-digest",
                'anemometer' : "https://github.com/box/Anemometer/archive/master.tar.gz",
                }

    ee_utils = {
                'phpmemcacheadmin' : "http://phpmemcacheadmin.googlecode.com/files/phpMemcachedAdmin-1.2.2-r262.tar.gz",
                'cleancache' : "https://raw.githubusercontent.com/rtCamp/eeadmin/master/cache/nginx/clean.php",
                'opcache' : "https://raw.github.com/rlerdorf/opcache-status/master/opcache.php",
                'webgrind' : "https://github.com/jokkedk/webgrind/archive/master.tar.gz",
                'ptqueryadvisor' : "http://bazaar.launchpad.net/~percona-toolkit-dev/percona-toolkit/2.1/download/head:/ptquerydigest-20110624220137-or26tn4expb9ul2a-16/pt-query-digest",
                'anemometer' : "https://github.com/box/Anemometer/archive/master.tar.gz",
              }

    ee_webmailstack = {
                        'vimbadmin': "https://github.com/opensolutions/ViMbAdmin/archive/{0}.tar.gz".format(ee_vimbadmin), 
                        'roundcube': "https://github.com/roundcube/roundcubemail/releases/download/{0}/roundcubemail-{0}.tar.gz".format(ee_roundcube)
                      }

    # Repo path
    ee_repo_file = "ee-repo.list"
    ee_repo_file_path = ("/etc/apt/sources.list.d/" + ee_repo_file)

    # Application dabase file path
    basedir = os.path.abspath(os.path.dirname('/var/lib/ee/'))
    ee_db_uri = 'sqlite:///' + os.path.join(basedir, 'ee.db')

    def __init__(self):
        pass
