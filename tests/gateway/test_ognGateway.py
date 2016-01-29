import unittest
import unittest.mock as mock

from ogn.gateway.client import ognGateway
from ogn.gateway.settings import APRS_APP_NAME, APRS_APP_VER


class GatewayTest(unittest.TestCase):
    def test_initialisation(self):
        self.gw = ognGateway(aprs_user='testuser', aprs_filter='')
        self.assertEqual(self.gw.aprs_user, 'testuser')
        self.assertEqual(self.gw.aprs_filter, '')

    @mock.patch('ogn.gateway.client.socket')
    def test_connect(self, mock_socket):
        self.gw = ognGateway(aprs_user='testuser', aprs_filter='')
        self.gw.connect()
        self.gw.sock.send.assert_called_once_with('user testuser pass -1 vers {} {}\n'.format(APRS_APP_NAME, APRS_APP_VER).encode('ascii'))
        self.gw.sock.makefile.asser_called_once_with('rw')

    @mock.patch('ogn.gateway.client.socket')
    def test_disconnect(self, mock_socket):
        self.gw = ognGateway(aprs_user='testuser', aprs_filter='')
        self.gw.connect()
        self.gw.disconnect()
        self.gw.sock.shutdown.assert_called_once_with(0)
        self.gw.sock.close.assert_called_once_with()