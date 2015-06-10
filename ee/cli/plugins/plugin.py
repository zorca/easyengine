"""EasyEngine plugin manager"""
from cement.core.controller import CementBaseController, expose
from cement.core import handler, hook
from ee.core.api_return import api_return
import pip


def ee_plugin_hook(app):
    # do something with the ``app`` object here.
    pass


class EEPluginController(CementBaseController):
    class Meta:
        label = 'plugin'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'plugin manager for EasyEngine'
        arguments = [
            (['-y', '--yes'],
                dict(help='Default yes action', action='store_true')),
            (['plugin_name'],
                dict(help='Plugin name to install/uninstall/search/upgrade',
                     nargs='?')),
            ]
        usage = "ee plugin (command) [options]"

    @expose(hide=True)
    def default(self):
        """default action of ee plugin command"""
        self.app.args.print_help()

    @expose(help="Install plugins")
    def install(self):
        url = ("http://epm.rtcamp.net:3000/info?name={0}"
               .format(self.app.pargs.plugin_name))
        pinfo = api_return(url)
        try:
            pip.main(['install', pinfo[0]['file']])
        except Exception as e:
            return False

    @expose(help="Uninstall plugin")
    def uninstall(self):
        """Start Uninstallation of plugins"""
        try:
            pip.main(['uninstall', self.app.pargs.plugin_name])
        except Exception as e:
            return False

    @expose(help="List installed plugins")
    def list(self):
        """List installed plugins"""
        pass

    @expose(help="Search plugins")
    def search(self):
        """Search plugins into EPM respository"""
        url = ("http://epm.rtcamp.net:3000/query?name={0}"
               .format(self.app.pargs.plugin_name))
        pinfo = api_return(url)
        self.log.info("Available Packages:")
        for info in pinfo:
            self.log.info(info['name'])

    @expose(help="Upgrade installed plugins")
    def upgrade(self):
        """Upgrade installed plugins"""
        pass

    @expose(help="Display plugin information")
    def info(self):
        """Display plugin information"""
        url = ("http://epm.rtcamp.net:3000/info?name={0}"
               .format(self.app.pargs.plugin_name))
        pinfo = api_return(url)
        self.log.info("Package Infomation:")
        self.log.info("Name: {0}".format(pinfo[0]['name']))
        self.log.info("Type: {0}".format(pinfo[0]['type']))
        self.log.info("Version: {0}".format(pinfo[0]['version']))
        self.log.info("Description: {0}".format(pinfo[0]['description']))
        self.log.info("Author: {0}".format(pinfo[0]['author']))
        self.log.info("Package URL: {0}".format(pinfo[0]['plugin_url']))
        self.log.info("Repo URL: {0}".format(pinfo[0]['repo_url']))
        self.log.info("License: {0}".format(pinfo[0]['license']))
        self.log.info("Price in $: {0}".format(pinfo[0]['price']))

    @expose(help="Enable installed plugin")
    def enable(self):
        """Enable installed plugin"""
        pass

    @expose(help="Disable installed plugin")
    def disable(self):
        """Disable installed plugin"""
        pass


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    handler.register(EEPluginController)

    # register a hook (function) to run after arguments are parsed.
    hook.register('post_argument_parsing', ee_plugin_hook)
