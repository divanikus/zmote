"""Support for zMote IR devices."""
import logging
import inspect
import socket
import voluptuous as vol

from requests import Session
from homeassistant.components import remote
from homeassistant.components.remote import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_NAME,
    DEVICE_DEFAULT_NAME,
)
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5000

CONF_COMMANDS = "commands"
CONF_DATA = "data"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_DEVICES): vol.All(
            cv.ensure_list,
            [
                {
                    vol.Optional(CONF_NAME): cv.string,
                    vol.Required(CONF_COMMANDS): vol.All(
                        cv.ensure_list,
                        [
                            {
                                vol.Required(CONF_NAME): cv.string,
                                vol.Required(CONF_DATA): cv.string,
                            }
                        ],
                    ),
                }
            ],
        ),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the zmote connection and devices."""
    zmc = Connector(
        transport=HTTPTransport(config.get(CONF_HOST))
    )

    devices = []
    for data in config.get(CONF_DEVICES):
        name = data.get(CONF_NAME)
        cmddatas = {}
        for cmd in data.get(CONF_COMMANDS):
            cmdname = cmd[CONF_NAME].strip()
            if not cmdname:
                cmdname = '""'
            cmddata = cmd[CONF_DATA].strip()
            if not cmddata:
                cmddata = '""'
            cmddatas[cmdname]= cmddata
        devices.append(Zmote2IRRemote(zmc, name, cmddatas))
    add_entities(devices, True)
    return True

class HTTPTransport(object):
    def __init__(self, ip):
        self._ip = ip

        self._session = None
        self._uuid = None

        self._logger = _LOGGER
        self._logger.debug('{0}(); ip={1}'.format(
            inspect.currentframe().f_code.co_name, repr(ip)
        ))

    def get_uuid(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        uuid = self._session.get(
            'http://{0}/uuid'.format(self._ip),
            timeout=5,
        ).text.split(',')[-1].strip()

        self._logger.debug('{0}(); uuid={1}'.format(
            inspect.currentframe().f_code.co_name, repr(uuid)
        ))

        return uuid

    def connect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        self._session = Session()
        self._uuid = self.get_uuid()

        self._logger.debug('{0}(); session={1}, uuid={2}'.format(
            inspect.currentframe().f_code.co_name, self._session, repr(self._uuid)
        ))

    def call(self, data):
        self._logger.debug('{0}({1})'.format(
            inspect.currentframe().f_code.co_name, repr(data),
        ))

        output = self._session.post(
            url='http://{0}/v2/{1}'.format(
                self._ip, self._uuid,
            ),
            data=data,
            timeout=5,
        ).text

        self._logger.debug('{0}({1}); output={2}'.format(
            inspect.currentframe().f_code.co_name, repr(data), repr(output)
        ))

        return output

    def disconnect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name,
        ))

        self._session = None

class Connector(object):
    def __init__(self, transport):
        self._transport = transport

        self._logger = _LOGGER
        self._logger.debug('{0}(); transport={1}'.format(
            inspect.currentframe().f_code.co_name, transport
        ))

    def connect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name
        ))

        self._transport.connect()

    def send(self, data):
        self._logger.debug('{0}({1})'.format(
            inspect.currentframe().f_code.co_name, repr(data)
        ))

        data = data.split('sendir,')[-1]

        output = self._transport.call('sendir,{0}'.format(data))

        self._logger.debug('{0}({1}); output={2}'.format(
            inspect.currentframe().f_code.co_name, repr(data), repr(output)
        ))

        return output

    def learn(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name
        ))

        data = self._transport.call('get_IRL')

        self._logger.debug('{0}(); data={1}'.format(
            inspect.currentframe().f_code.co_name, repr(data)
        ))

        return data.split('sendir,')[-1]

    def disconnect(self):
        self._logger.debug('{0}()'.format(
            inspect.currentframe().f_code.co_name
        ))

        self._transport.disconnect()

class Zmote2IRRemote(remote.RemoteDevice):
    """Device that sends commands to an zmote IR device."""

    def __init__(self, zmc, name, cmds):
        """Initialize device."""
        self.zmc = zmc
        self._power = False
        self._name = name or DEVICE_DEFAULT_NAME
        self._cmds = cmds

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._power

    def toggle(self, **kwargs):
        """Toggle device."""
        if "TOGGLE" in self._cmds and "OFF" in self._cmds:
            self._power = not self._power
            self.send_command(["TOGGLE"])
            self.schedule_update_ha_state()

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if "OFF" in self._cmds:
            self._power = True
        else:
            self._power = False
        self.send_command(["ON"])
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._power = False
        self.send_command(["OFF"])
        self.schedule_update_ha_state()

    def send_command(self, command, **kwargs):
        """Send a command to one device."""
        self.zmc.connect()
        for single_command in command:
            if single_command in self._cmds:
                self.zmc.send(self._cmds[single_command])
        self.zmc.disconnect()

    def update(self):
        """Update the device."""
