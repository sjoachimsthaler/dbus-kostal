#!/usr/bin/env python

# vim: ts=2 sw=2 et


# import normal packages
import platform 
import logging

import logging.handlers

import sys
import os

import sys

if sys.version_info.major == 2:

    import gobject

else:

    from gi.repository import GLib as gobject

import sys
import time

import requests # for http GET

import configparser # for config/ini file
 

# our own packages from victron

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))

from vedbus import VeDbusService



class DbusKostalService:
  def __init__(self, paths, productname='Kostal PV', connection='Kostal Xml XmlService'):

    config = self._getConfig()

    deviceinstance = int(config['DEFAULT']['DeviceInstance'])

    customname = config['DEFAULT']['CustomName']

    role = config['DEFAULT']['Role']


    allowed_roles = ['pvinverter']

    if role in allowed_roles:

        servicename = 'com.victronenergy.' + role

    else:

        logging.error("Configured Role: %s is not in the allowed list")

        exit()


    if role == 'pvinverter':

        productid = 0xA144

    else:

        productid = 45069


    self._dbusservice = VeDbusService("{}.http_{:02d}".format(servicename, deviceinstance))

    self._paths = paths
 

    logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))
 

    # Create the management objects, as specified in the ccgx dbus-api document

    self._dbusservice.add_path('/Mgmt/ProcessName', __file__)

    self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())

    self._dbusservice.add_path('/Mgmt/Connection', connection)
 

    # Create the mandatory objects

    self._dbusservice.add_path('/DeviceInstance', deviceinstance)

    self._dbusservice.add_path('/ProductId', productid)

    self._dbusservice.add_path('/DeviceType', 345) # found on https://www.sascha-curth.de/projekte/005_Color_Control_GX.html#experiment - should be an ET340 Engerie Meter

    self._dbusservice.add_path('/ProductName', productname)

    self._dbusservice.add_path('/CustomName', customname)

    self._dbusservice.add_path('/Latency', None)

    self._dbusservice.add_path('/FirmwareVersion', 0.3)

    self._dbusservice.add_path('/HardwareVersion', 0)

    self._dbusservice.add_path('/Connected', 1)

    self._dbusservice.add_path('/Role', role)

    self._dbusservice.add_path('/Position', self._getKostalPosition()) # normaly only needed for pvinverter

    self._dbusservice.add_path('/Serial', self._getShellySerial())

    self._dbusservice.add_path('/UpdateIndex', 0)
 

    # add path values to dbus

    for path, settings in self._paths.items():

      self._dbusservice.add_path(

        path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)
 

    # last update

    self._lastUpdate = 0
 

    # add _update function 'timer'

    gobject.timeout_add(500, self._update) # pause 500ms before the next request
    

    # add _signOfLife 'timer' to get feedback in log every 5minutes

    gobject.timeout_add(self._getSignOfLifeInterval()*60*1000, self._signOfLife)
 

  def _getShellySerial(self):

    meter_data = self._getKostalData()  
    

    if not meter_data['root']['Device']['@Serial']:

        raise ValueError("Response does not contain 'mac' attribute")
    

    serial = meter_data['root']['Device']['@Serial']
    return serial
 
 

  def _getConfig(self):

    config = configparser.ConfigParser()

    config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))

    return config;
 
 

  def _getSignOfLifeInterval(self):

    config = self._getConfig()

    value = config['DEFAULT']['SignOfLifeLog']
    

    if not value: 

        value = 0
    
    return int(value)
 
 

  def _getKostalPosition(self):

    config = self._getConfig()

    value = config['DEFAULT']['Position']
    

    if not value: 

        value = 0
    
    return int(value)
 
 

  def _getKostalStatusUrl(self):

    config = self._getConfig()

    accessType = config['DEFAULT']['AccessType']
    

    if accessType == 'OnPremise': 

        URL = "http://%s/measurements.xml" % (config['ONPREMISE']['Host'])

        URL = URL.replace(":@", "")

    else:

        raise ValueError("AccessType %s is not supported" % (config['DEFAULT']['AccessType']))
    

    return URL
    
 

  def _getKostalData(self):

    URL = self._getKostalStatusUrl()

    meter_r = requests.get(url = URL, timeout=5)
    

    # check for response

    if not meter_r:

        raise ConnectionError("No response from Kostal - %s" % (URL))
    
    import xmltodict

    meter_data = xmltodict.parse(meter_r.text)
    

    # check for Json

    if not meter_data:

        raise ValueError("Converting response to Xml failed")
    
    
    return meter_data
 
 

  def _signOfLife(self):

    logging.info("--- Start: sign of life ---")

    logging.info("Last _update() call: %s" % (self._lastUpdate))

    logging.info("Last '/Ac/Power': %s" % (self._dbusservice['/Ac/Power']))

    logging.info("--- End: sign of life ---")

    return True
 

  def _update(self):   

    try:

      #get data from Kostal

      meter_data = self._getKostalData()

      config = self._getConfig()
       

      #send data to DBus

      #self._dbusservice['/Ac/Power'] = meter_data['total_power']

      if (config['DEFAULT']['Phase'] == '1'):
        self._dbusservice['/Ac/L1/Voltage'] = float(meter_data['root']['Device']['Measurements']['Measurement'][0]['@Value'])

        x = meter_data['root']['Device']['Measurements']['Measurement'][1]
        current = 0
        if "@Value" in x:
            current = x['@Value']
        self._dbusservice['/Ac/L1/Current'] = float(current)

        x = meter_data['root']['Device']['Measurements']['Measurement'][2]
        power = 0
        if "@Value" in x:
            power = x['@Value']
        self._dbusservice['/Ac/L1/Power'] = float(power)
        self._dbusservice['/Ac/Power'] = float(power)

      if (config['DEFAULT']['Phase'] == '2'):
        self._dbusservice['/Ac/L2/Voltage'] = float(meter_data['root']['Device']['Measurements']['Measurement'][0]['@Value'])

        x = meter_data['root']['Device']['Measurements']['Measurement'][1]
        current = 0
        if "@Value" in x:
            current = x['@Value']
        self._dbusservice['/Ac/L2/Current'] = float(current)

        x = meter_data['root']['Device']['Measurements']['Measurement'][2]
        power = 0
        if "@Value" in x:
            power = x['@Value']
        self._dbusservice['/Ac/L2/Power'] = float(power)
        self._dbusservice['/Ac/Power'] = float(power)

      if (config['DEFAULT']['Phase'] == '3'):
        self._dbusservice['/Ac/L3/Voltage'] = float(meter_data['root']['Device']['Measurements']['Measurement'][0]['@Value'])

        x = meter_data['root']['Device']['Measurements']['Measurement'][1]
        current = 0
        if "@Value" in x:
            current = x['@Value']
        self._dbusservice['/Ac/L3/Current'] = float(current)

        x = meter_data['root']['Device']['Measurements']['Measurement'][2]
        power = 0
        if "@Value" in x:
            power = x['@Value']
        self._dbusservice['/Ac/L3/Power'] = float(power)
        self._dbusservice['/Ac/Power'] = float(power)

      

      # self._dbusservice['/Ac/L1/Voltage'] = meter_data['emeters'][0]['voltage']

      # self._dbusservice['/Ac/L2/Voltage'] = meter_data['emeters'][1]['voltage']

      # self._dbusservice['/Ac/L3/Voltage'] = meter_data['emeters'][2]['voltage']

      # self._dbusservice['/Ac/L1/Current'] = meter_data['emeters'][0]['current']

      # self._dbusservice['/Ac/L2/Current'] = meter_data['emeters'][1]['current']

      # self._dbusservice['/Ac/L3/Current'] = meter_data['emeters'][2]['current']

      # self._dbusservice['/Ac/L1/Power'] = meter_data['emeters'][0]['power']

      # self._dbusservice['/Ac/L2/Power'] = meter_data['emeters'][1]['power']

      # self._dbusservice['/Ac/L3/Power'] = meter_data['emeters'][2]['power']

      # self._dbusservice['/Ac/L1/Energy/Forward'] = (meter_data['emeters'][0]['total']/1000)

      # self._dbusservice['/Ac/L2/Energy/Forward'] = (meter_data['emeters'][1]['total']/1000)

      # self._dbusservice['/Ac/L3/Energy/Forward'] = (meter_data['emeters'][2]['total']/1000)

      # self._dbusservice['/Ac/L1/Energy/Reverse'] = (meter_data['emeters'][0]['total_returned']/1000) 

      # self._dbusservice['/Ac/L2/Energy/Reverse'] = (meter_data['emeters'][1]['total_returned']/1000) 

      # self._dbusservice['/Ac/L3/Energy/Reverse'] = (meter_data['emeters'][2]['total_returned']/1000) 
      

      # Old version

      #self._dbusservice['/Ac/Energy/Forward'] = self._dbusservice['/Ac/L1/Energy/Forward'] + self._dbusservice['/Ac/L2/Energy/Forward'] + self._dbusservice['/Ac/L3/Energy/Forward']

      #self._dbusservice['/Ac/Energy/Reverse'] = self._dbusservice['/Ac/L1/Energy/Reverse'] + self._dbusservice['/Ac/L2/Energy/Reverse'] + self._dbusservice['/Ac/L3/Energy/Reverse'] 
      

      # New Version - from xris99

      #Calc = 60min * 60 sec / 0.500 (refresh interval of 500ms) * 1000

      # if (self._dbusservice['/Ac/Power'] > 0):

      #      self._dbusservice['/Ac/Energy/Forward'] = self._dbusservice['/Ac/Energy/Forward'] + (self._dbusservice['/Ac/Power']/(60*60/0.5*1000))            

      # if (self._dbusservice['/Ac/Power'] < 0):

      #      self._dbusservice['/Ac/Energy/Reverse'] = self._dbusservice['/Ac/Energy/Reverse'] + (self._dbusservice['/Ac/Power']*-1/(60*60/0.5*1000))

      

      #logging

      # logging.debug("House Consumption (/Ac/Power): %s" % (self._dbusservice['/Ac/Power']))

      # logging.debug("House Forward (/Ac/Energy/Forward): %s" % (self._dbusservice['/Ac/Energy/Forward']))

      # logging.debug("House Reverse (/Ac/Energy/Revers): %s" % (self._dbusservice['/Ac/Energy/Reverse']))

      # logging.debug("---");
      

      # increment UpdateIndex - to show that new data is available an wrap

      self._dbusservice['/UpdateIndex'] = (self._dbusservice['/UpdateIndex'] + 1 ) % 256


      #update lastupdate vars

      self._lastUpdate = time.time()

    except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.Timeout, ConnectionError) as e:

       logging.critical('Error getting data from Kostal - check network or Kostal status. Setting power values to 0. Details: %s', e, exc_info=e)       

      #  self._dbusservice['/Ac/L1/Power'] = 0                                       

      #  self._dbusservice['/Ac/L2/Power'] = 0                                       

      #  self._dbusservice['/Ac/L3/Power'] = 0

      #  self._dbusservice['/Ac/Power'] = 0

       self._dbusservice['/UpdateIndex'] = (self._dbusservice['/UpdateIndex'] + 1 ) % 256        

    except Exception as e:

       logging.critical('Error at %s', '_update', exc_info=e)
       

    # return true, otherwise add_timeout will be removed from GObject - see docs http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--timeout-add

    return True
 

  def _handlechangedvalue(self, path, value):

    logging.debug("someone else updated %s to %s" % (path, value))

    return True # accept the change





def getLogLevel():

  config = configparser.ConfigParser()

  config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))

  logLevelString = config['DEFAULT']['LogLevel']
  

  if logLevelString:

    level = logging.getLevelName(logLevelString)

  else:

    level = logging.INFO
    
  return level



def main():

  #configure logging

  logging.basicConfig(      format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',

                            datefmt='%Y-%m-%d %H:%M:%S',

                            level=getLogLevel(),

                            handlers=[

                                logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),

                                logging.StreamHandler()

                            ])
 

  try:

      logging.info("Start");
  

      from dbus.mainloop.glib import DBusGMainLoop

      # Have a mainloop, so we can send/receive asynchronous calls to and from dbus

      DBusGMainLoop(set_as_default=True)
     

      #formatting 

      _kwh = lambda p, v: (str(round(v, 2)) + ' kWh')

      _a = lambda p, v: (str(round(v, 1)) + ' A')

      _w = lambda p, v: (str(round(v, 1)) + ' W')

      _v = lambda p, v: (str(round(v, 1)) + ' V')   
     

      #start our main-service

      pvac_output = DbusKostalService(

        paths={

          '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh}, # energy bought from the grid

          '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh}, # energy sold to the grid

          '/Ac/Power': {'initial': 0, 'textformat': _w},
          

          '/Ac/Current': {'initial': 0, 'textformat': _a},

          '/Ac/Voltage': {'initial': 0, 'textformat': _v},
          

          '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},

          '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},

          '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},

          '/Ac/L1/Current': {'initial': 0, 'textformat': _a},

          '/Ac/L2/Current': {'initial': 0, 'textformat': _a},

          '/Ac/L3/Current': {'initial': 0, 'textformat': _a},

          '/Ac/L1/Power': {'initial': 0, 'textformat': _w},

          '/Ac/L2/Power': {'initial': 0, 'textformat': _w},

          '/Ac/L3/Power': {'initial': 0, 'textformat': _w},

          '/Ac/L1/Energy/Forward': {'initial': 0, 'textformat': _kwh},

          '/Ac/L2/Energy/Forward': {'initial': 0, 'textformat': _kwh},

          '/Ac/L3/Energy/Forward': {'initial': 0, 'textformat': _kwh},

          '/Ac/L1/Energy/Reverse': {'initial': 0, 'textformat': _kwh},

          '/Ac/L2/Energy/Reverse': {'initial': 0, 'textformat': _kwh},

          '/Ac/L3/Energy/Reverse': {'initial': 0, 'textformat': _kwh},

        })
     

      logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')

      mainloop = gobject.MainLoop()
      mainloop.run()            

  except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:

    logging.critical('Error in main type %s', str(e))

  except Exception as e:

    logging.critical('Error at %s', 'main', exc_info=e)

if __name__ == "__main__":
  main()

