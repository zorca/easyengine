from sqlalchemy import Column, DateTime, String, Integer, Boolean
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from ee.core.logging import Log
from ee.core.database import db_session
from ee.cli.plugins.models import PluginDB
import sys
import glob


def addNewPlugin(self, plugin, plugin_type, plugin_version,
                 plugin_enabled):
    """
    Add New Site record information into ee database.
    """
    try:
        newRec = PluginDB(plugin, plugin_type, plugin_version,
                          plugin_enabled)
        db_session.add(newRec)
        db_session.commit()
    except Exception as e:
        Log.error(self, "Unable to add site to database")


def getPluginInfo(self, plugin):
    """
        Retrieves site record from ee databse
    """
    try:
        q = PluginDB.query.filter(PluginDB.pluginname == plugin).first()
        return q
    except Exception as e:
        Log.error(self, "Unable to query database for site info")


def updatePluginInfo(self, plugin, type='', version='', enabled=True):
    """updates site record in database"""
    try:
        q = PluginDB.query.filter(PluginDB.pluginname == plugin).first()
    except Exception as e:
        Log.error(self, "Unable to query database for site info")

    if not q:
        Log.error(self, "{0} is not installed".format(site))

    # Check if new record matches old if not then only update database
    if stype and q.site_type != stype:
        q.site_type = stype

    if cache and q.cache_type != cache:
        q.cache_type = cache

    if q.is_enabled != enabled:
        q.is_enabled = enabled

    if ssl and q.is_ssl != ssl:
        q.is_ssl = ssl

    if db_name and q.db_name != db_name:
        q.db_name = db_name

    if db_user and q.db_user != db_user:
        q.db_user = db_user

    if db_user and q.db_password != db_password:
        q.db_password = db_password

    if db_host and q.db_host != db_host:
        q.db_host = db_host

    if webroot and q.site_path != webroot:
        q.site_path = webroot

    if (hhvm is not None) and (q.is_hhvm is not hhvm):
        q.is_hhvm = hhvm

    if (pagespeed is not None) and (q.is_pagespeed is not pagespeed):
        q.is_pagespeed = pagespeed

    try:
        q.created_on = func.now()
        db_session.commit()
    except Exception as e:
        Log.debug(self, "{0}".format(e))
        Log.error(self, "Unable to update site info in application database.")


def deletePluginInfo(self, plugin):
    """Delete site record in database"""
    try:
        q = PluginDB.query.filter(PluginDB.pluginname == plugin).first()
    except Exception as e:
        Log.debug(self, "{0}".format(e))
        Log.error(self, "Unable to query database")

    if not q:
        Log.error(self, "{0} does not exist".format(site))

    try:
        db_session.delete(q)
        db_session.commit()
    except Exception as e:
        Log.error(self, "Unable to delete site from application database.")


def getAllplugins(self):
    """
        1. returns all records from ee database
    """
    try:
        q = PluginDB.query.all()
        return q
    except Exception as e:
        Log.error(self, "Unable to query database")
