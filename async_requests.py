import asyncio
from PyQt5.QtCore import QObject, QUrl, QByteArray, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPixmap


class _AsyncRequestHandler(QObject):
    finished = pyqtSignal(QNetworkReply)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.finished.emit)

    async def send(self, request: QNetworkRequest, method: str = "GET", data: bytes = None) -> QNetworkReply:
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def handle_finished(reply: QNetworkReply):
            self.finished.disconnect(handle_finished)
            future.set_result(reply)

        self.finished.connect(handle_finished)

        method = method.upper()
        if method == "GET":
            reply = self.manager.get(request)
        elif method == "POST":
            reply = self.manager.post(request, QByteArray(data or b""))
        elif method == "PUT":
            reply = self.manager.put(request, QByteArray(data or b""))
        elif method == "DELETE":
            reply = self.manager.deleteResource(request)
        elif method == "HEAD":
            reply = self.manager.head(request)
        elif method == "PATCH":
            reply = self.manager.sendCustomRequest(request, b"PATCH", QByteArray(data or b""))
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        return await future


class AsyncRequests:
    _handler: _AsyncRequestHandler = None

    @classmethod
    def init(cls, app):
        if cls._handler is None:
            cls._handler = _AsyncRequestHandler(app)

    @classmethod
    async def request(cls, method: str, url: str, data: bytes = None, headers: dict = None, raw: bool = False):
        if cls._handler is None:
            raise RuntimeError("")

        request = QNetworkRequest(QUrl(url))
        if headers:
            for k, v in headers.items():
                request.setRawHeader(k.encode(), v.encode())

        reply = await cls._handler.send(request, method=method, data=data)
        return cls._read_reply(reply, raw=raw)

    @classmethod
    async def get(cls, url: str, headers: dict = None, raw: bool = False):
        return await cls.request("GET", url, headers=headers, raw=raw)

    @classmethod
    async def post(cls, url: str, data: bytes, headers: dict = None, raw: bool = False):
        return await cls.request("POST", url, data=data, headers=headers, raw=raw)

    @staticmethod
    def _read_reply(reply: QNetworkReply, raw: bool = False):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            msg = reply.errorString()
            reply.deleteLater()
            raise Exception(f"Network error: {msg}")
        data = reply.readAll().data()
        reply.deleteLater()
        return data if raw else data.decode("utf-8", errors="replace")


class AsyncPixmapLoader(QObject):
    finished = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.on_finished)

    def start(self):
        request = QNetworkRequest(QUrl(self.url))
        from updater import Updater
        request.setRawHeader(b"User-Agent",b"Mozilla/5.0 (compatible; Universal Resonance Stone/" + Updater.VERSION.encode('utf-8') + b")")
        self.reply = self.manager.get(request)
        self.reply.finished.connect(self.handle_reply_finished)

    def handle_reply_finished(self):
        if self.reply.error():
            self.error.emit(f"Network error: {self.reply.errorString()}")
            self.reply.deleteLater()
            return

        data = self.reply.readAll()
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            self.error.emit("Failed to load image data")
            self.reply.deleteLater()
            return

        self.finished.emit(pixmap)
        self.reply.deleteLater()

    def on_finished(self, reply):
        pass