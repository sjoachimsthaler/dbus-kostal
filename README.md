# dbus-kostal
Integrate Kostal Piko MP Plus PV inverter into [Victron Energies Venus OS](https://github.com/victronenergy/venus)

## Purpose
With the scripts in this repo it should be easy possible to install, uninstall, restart a service that connects the Kostal Piko MP Plus inverter to the VenusOS and GX devices from Victron.
Idea is basend on @RalfZim project linked below.



## Inspiration
This project is my first on GitHub and with the Victron Venus OS, so I took some ideas and approaches from the following projects - many thanks for sharing the knowledge:
- https://github.com/RalfZim/venus.dbus-fronius-smartmeter
- https://github.com/victronenergy/dbus-smappee
- https://github.com/Louisvdw/dbus-serialbattery
- https://community.victronenergy.com/idea/114716/power-meter-lib-for-modbus-rtu-based-meters-from-a.html - [Old Thread](https://community.victronenergy.com/questions/85564/eastron-sdm630-modbus-energy-meter-community-editi.html)
- https://github.com/fabian-lauer/dbus-shelly-3em-smartmeter/blob/main/README.md

## How it works
### My setup
- Shelly 3EM with latest firmware (20220209-094824/v1.11.8-g8c7bb8d)
  - 3-Phase installation (normal for Germany)
  - Connected to Wifi network "A"
  - IP 192.168.2.13/24  
- Victron Energy Multiplus II GX with Venus OS - Firmware v3.22
  - Connected to Wifi network "A"
  - IP 192.168.10.20/24

### Details / Process
As mentioned above the script is inspired by @RalfZim fronius smartmeter implementation.
So what is the script doing:
- Running as a service
- connecting to DBus of the Venus OS `com.victronenergy.pvinverter.http_40`
- After successful DBus connection Kostal PV Inverter is accessed via REST-API - simply the /status is called and a JSON is returned with all details
- Serial/MAC is taken from the response as device serial
- Paths are added to the DBus with default value 0 - including some settings like name, etc
- After that a "loop" is started which pulls Kostal Piko data every 750ms from the REST-API and updates the values in the DBus

Thats it 😄




## Install & Configuration
### Get the code
Just grap a copy of the main branche and copy them to `/data/dbus-kostal`.
After that call the install.sh script.

The following script should do everything for you:
```
wget https://github.com/sjoachimsthaler/dbus-kostal/archive/refs/heads/main.zip
unzip main.zip "dbus-kostal-main/*" -d /data
mv /data/dbus-kostal-main /data/dbus-kostal
chmod a+x /data/dbus-kostal/install.sh
/data/dbus-kostal/install.sh
rm main.zip
```
⚠️ Check configuration after that - because service is already installed an running and with wrong connection data (host, username, pwd) you will spam the log-file


Sometimes I get an error that xmltodict is not installed. It can be installed with the command
```
python3 -m pip install xmltodict
```

### Change config.ini
Within the project there is a file `/data/dbus-kostal/config.ini` - just change the values - most important is the host, username and password in section "ONPREMISE". More details below:

| Section  | Config vlaue | Explanation |
| ------------- | ------------- | ------------- |
| DEFAULT  | AccessType | Fixed value 'OnPremise' |
| DEFAULT  | SignOfLifeLog  | Time in minutes how often a status is added to the log-file `current.log` with log-level INFO |
| DEFAULT  | CustomName  | Name of your device - usefull if you want to run multiple versions of the script |
| DEFAULT  | DeviceInstance  | DeviceInstanceNumber e.g. 40 |
| DEFAULT  | Role | use 'GRID' or 'PVINVERTER' to set the type of the shelly 3EM |
| DEFAULT  | Position | Available Postions: 0 = AC, 1 = AC-Out 1, AC-Out 2 |
| DEFAULT  | LogLevel  | Define the level of logging - lookup: https://docs.python.org/3/library/logging.html#levels |
| ONPREMISE  | Host | IP or hostname of on-premise Shelly 3EM web-interface |
| ONPREMISE  | Username | Username for htaccess login - leave blank if no username/password required |
| ONPREMISE  | Password | Password for htaccess login - leave blank if no username/password required |
| ONPREMISE  | L1Position | Which input on the Shelly in 3-phase grid is supplying a single Multi |


## Used documentation
- https://github.com/victronenergy/venus/wiki/dbus#grid   DBus paths for Victron namespace GRID
- https://github.com/victronenergy/venus/wiki/dbus#pv-inverters   DBus paths for Victron namespace PVINVERTER
- https://github.com/victronenergy/venus/wiki/dbus-api   DBus API from Victron
- https://www.victronenergy.com/live/ccgx:root_access   How to get root access on GX device/Venus OS

## Discussions on the web
