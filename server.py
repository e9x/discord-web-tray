#!/usr/bin/env python3
import signal
import sys
from collections import namedtuple
from json import loads, JSONDecodeError
from PyQt5 import QtWidgets, QtGui, QtWebSockets, QtNetwork, QtCore

# port to run websocket server on
serverPort = 39819

# allow more than one tray icon
allowMultipleTrays = True

# end of config


IconUpdate = namedtuple("IconUpdate", ["icon", "flash", "tooltipSuffix"])


def parse_icon_update(message: str):
    data = loads(message)

    if type(data) != dict:
        raise TypeError("message was not a dict")

    icon = data["icon"]
    flash = data["flash"]
    tooltipSuffix = data["tooltipSuffix"]

    if not icon in tray_icons:
        raise TypeError("icon was not a valid tray icon")

    if type(flash) != bool:
        raise TypeError("flash was not bool")

    if type(tooltipSuffix) != str:
        raise TypeError("tooltipSuffix was not string")

    return IconUpdate(icon, flash, tooltipSuffix)


class DiscordTray(QtWidgets.QSystemTrayIcon):
    appName = "Discord"

    def __init__(self, socket, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, parent)
        self.socket = socket
        self.menu = QtWidgets.QMenu(self.parent())
        self.menu.addAction(tray_icons["default"], self.appName).setDisabled(True)
        self.menu.addSeparator().setDisabled(True)
        self.menu.addAction("Toggle").triggered.connect(self.toggle)
        self.menu.addSeparator().setDisabled(True)
        self.menu.addAction("Quit").triggered.connect(self.quit)
        self.setContextMenu(self.menu)
        self.activated.connect(self.show_menu)
        self.update(IconUpdate("default", False, ""))

    def update(self, data: IconUpdate):
        print(
            "Icon update:",
            data,
        )
        self.setIcon(tray_icons[data.icon])
        self.setToolTip(self.appName + data.tooltipSuffix)

    def toggle(self):
        wss_thread.socket_toggle.emit(self.socket)

    def quit(self):
        wss_thread.socket_close.emit(self.socket)

    def show_menu(self, reason):
        if reason == self.Trigger:
            self.toggle()


class DiscordWSS(QtWebSockets.QWebSocketServer):
    clients = []

    def __init__(self, parent=None):
        QtWebSockets.QWebSocketServer.__init__(
            self, None, QtWebSockets.QWebSocketServer.SslMode.NonSecureMode, parent
        )

        self.newConnection.connect(self.onNewConnection)

    def onNewConnection(self):
        socket = self.nextPendingConnection()

        if not allowMultipleTrays and len(self.clients) != 0:
            print("Client connected but there's too many. Closing...")
            socket.close()
            return

        print("Client connected")
        self.clients.append(socket)

        wss_thread.tray_create.emit(socket)

        def handleMessage(message):
            wss_thread.tray_update.emit(socket, parse_icon_update(message))

        def handleDisconnect():
            print("Client disconnected")
            wss_thread.tray_delete.emit(socket)
            self.clients.remove(socket)

        socket.textMessageReceived.connect(handleMessage)
        socket.disconnected.connect(handleDisconnect)


def socket_toggle(socket: QtWebSockets.QWebSocket):
    socket.sendTextMessage("toggle")


def socket_close(socket: QtWebSockets.QWebSocket):
    socket.sendTextMessage("close")
    socket.close()


class WSSThread(QtCore.QThread):
    tray_create = QtCore.pyqtSignal(QtWebSockets.QWebSocket)
    tray_update = QtCore.pyqtSignal(QtWebSockets.QWebSocket, IconUpdate)
    tray_delete = QtCore.pyqtSignal(QtWebSockets.QWebSocket)
    socket_toggle = QtCore.pyqtSignal(QtWebSockets.QWebSocket)
    socket_close = QtCore.pyqtSignal(QtWebSockets.QWebSocket)

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        server = DiscordWSS()

        self.socket_toggle.connect(socket_toggle)
        self.socket_close.connect(socket_close)

        serverAddress = QtNetwork.QHostAddress(
            QtNetwork.QHostAddress.SpecialAddress.LocalHost
        )

        if server.listen(serverAddress, serverPort):
            print(
                f"WebSocket server listening on ws://{serverAddress.toString()}:{serverPort}"
            )
            self.exec()


def tray_create(socket: QtWebSockets.QWebSocket):
    socket.widget = QtWidgets.QWidget()
    socket.tray = DiscordTray(socket, socket.widget)
    socket.tray.show()


def tray_update(socket: QtWebSockets.QWebSocket, data: IconUpdate):
    socket.tray.update(data)


def tray_delete(socket: QtWebSockets.QWebSocket):
    socket.tray.hide()
    socket.widget.destroy()


def main():
    global wss_thread, tray_icons

    app = QtWidgets.QApplication(sys.argv)

    tray_icons = {
        "default": QtGui.QIcon("icons/tray.png"),
        "unread": QtGui.QIcon("icons/tray-unread.png"),
        "warn": QtGui.QIcon("icons/tray-ping.png"),
    }

    wss_thread = WSSThread()

    wss_thread.tray_create.connect(tray_create)
    wss_thread.tray_update.connect(tray_update)
    wss_thread.tray_delete.connect(tray_delete)

    wss_thread.start()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
