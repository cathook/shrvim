#! /usr/bin/env python3

"""Main thread."""

import signal
import sys
import threading
import log

from cmd_ui import CmdUI
from tcp_server import TCPServer
from users_text_manager import UsersTextManager


class _ArgsError(Exception):
    """Exception raised by _Args."""
    pass

class _Args(object):
    """Arguments of this program.

    Attributes:
        port: Port number.
        user_list_filename: Default user list.
        save_filename: Name of the file to save the text.
    """
    DOCUMENT = '[usage] <port_number> <user_list_filename> <save_filename>\n'
    def __init__(self):
        if len(sys.argv) != 4:
            raise _ArgsError('Wrong length of arguments.')
        try:
            self.port = int(sys.argv[1])
        except ValueError as e:
            raise _ArgsError(e)
        self.user_list_filename = sys.argv[2]
        self.saved_filename = sys.argv[3]


class _ShrVimServerError(Exception):
    """Error raised by ShrVimServer."""
    pass

class ShrVimServer(threading.Thread):
    """Main class.

    Attributes:
        _users_text_manager: Instance of UsersTextManager.
        _tcp_server: Instance of TCPServer.
        _cmd_ui: Instance of CmdUI.
    """
    def __init__(self):
        """Constructor."""
        super(ShrVimServer, self).__init__()
        try:
            self._args = _Args()
        except _ArgsError as e:
            raise _ShrVimServerError(str(e) + '\n' + _Args.DOCUMENT)
        self._users_text_manager = UsersTextManager(self._args.saved_filename)
        self._tcp_server = TCPServer(self._args.port, self._users_text_manager)
        self._cmd_ui = CmdUI(['load %s' % self._args.user_list_filename],
                             self._users_text_manager, self._tcp_server, self)
        log.info.interface = self._cmd_ui
        log.error.interface = self._cmd_ui

    def run(self):
        """Starts the program."""
        self._tcp_server.start()
        self._cmd_ui.start()
        self._cmd_ui.join()
        self._tcp_server.join()

    def stop(self):
        """Exits the program."""
        self._cmd_ui.stop()
        self._tcp_server.stop()


class _SignalHandler(object):
    """Single handler.

    It will handle below the signals:
        SIGTERM, SIGINT - Exit the program.

    Attributes:
        _shrvim_server: Instance of ShrVimServer.
    """
    def __init__(self, shrvim_server):
        """Constructor.

        Args:
            shrvim_server: Instance of ShrVimServer.
        """
        self._shrvim_server = shrvim_server
        signal.signal(signal.SIGTERM, self._handler)
        signal.signal(signal.SIGINT, self._handler)

    def _handler(self, number, unused_frame):
        """Signal handler function.

        Args:
            number: The signal number to be handle.
        """
        if number in (signal.SIGTERM, signal.SIGINT):
            self._shrvim_server.stop()


def main():
    """Program entry point."""
    try:
        shrvim_server = ShrVimServer()
        _SignalHandler(shrvim_server)
        shrvim_server.start()
        shrvim_server.join()
    except _ShrVimServerError as e:
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
