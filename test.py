import json
import time
import requests
import threading
from PySide2.QtWidgets import QApplication, QTextEdit, QLineEdit, QComboBox
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtGui import QIcon
from PySide2.QtCore import Signal, QObject


class MySignals(QObject):
    text_print = Signal(QTextEdit, str)  # 表示这个信号发射时需要几个参数，这里定义了几个发射（emit）时就需要传几个
    text_clear = Signal(QTextEdit)


# 定义类
class Index:
    def __init__(self):
        qfile_stats = QFile("static/ui/index.ui")
        qfile_stats.open(QFile.ReadOnly)
        qfile_stats.close()
        self.ui = QUiLoader().load(qfile_stats)
        self.ui.button_send.clicked.connect(self.send)
        self.ui.button_clear.clicked.connect(self.clear_text)
        self.ms = MySignals()
        self.ms.text_print.connect(self.print_to_gui)
        self.ms.text_clear.connect(self.clear_to_gui)

    def clear_to_gui(self, ele):
        ele.clear()

    def clear_text(self):
        delete_thread = threading.Thread(target=self.clear_blocking_function)
        delete_thread.start()

    def clear_blocking_function(self):
        self.ms.text_clear.emit(self.ui.lineEdit)

    def print_to_gui(self, ele, text):
        ele.setPlainText(text)  # 在这里将文本设置到 QTextEdit 中

    def send(self):
        send_thread = threading.Thread(target=self.send_blocking_function)
        send_thread.start()

    def send_blocking_function(self):
        url = self.ui.findChild(QLineEdit, 'lineEdit')
        # 获取请求类型，分发到各api
        header = self.ui.findChild(QTextEdit, 'text_msg_head')
        body = self.ui.findChild(QTextEdit, 'text_msg_body')
        request_type = self.ui.comboBox.currentText().lower()
        request = QRequest(request_type, url, header, body)
        request.send()
        data = request.handle_response()
        self.ms.text_print.emit(self.ui.text_log, data)

        # self.ms.text_print.emit(self.ui.text_msg_head, url)


class QRequest(object):
    """
    接收网络请求参数
    根据请求类型不同分发到不同请求的函数来执行
    根据返回值数据类型不同分发到不同的函数来处理数据
    """

    def __init__(self, request_type, url, headers, body):
        self.request_type = request_type
        self.url = url.text()
        self.headers = headers.toPlainText()
        self.body = body.toPlainText()
        self.data_type = None
        self.response = None

    def send(self):
        response = getattr(self, self.request_type)()
        self.response = response

    def handle_response(self):
        print(self.response.json())
        print(self.request_type, self.response.headers)
        content_type = self.response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            return self.handle_json(self.response)
        else:
            return self.handle_unknown(self.response)

    def handle_json(self, data):
        json_data = data.json()
        print(json_data)
        output_text = ""
        json_list = json_data if type(json_data) == list else [json_data]
        for item in json_list:
            # output_text += f"ID: {item['id']}, Title: {item['title']}, Date: {item.get('date', 'N/A')}, Price: {item['price']}\n"
            output_text += f'{json.dumps(item, ensure_ascii=False)}\n'
        return output_text

    def handle_unknown(self, data):
        pass
    def get(self):
        response = requests.get(self.url, params=self.body)
        return response

    def post(self):
        response = requests.post(self.url, headers=json.loads(self.headers) if len(self.headers) != 0 else {},
                                 json=json.loads(self.body))  # json参数需要传字典，内部封装了序列化；如果有现成的json字符串就要用data参数（注意字典里是双引号）
        return response

    def put(self):
        response = requests.put(self.url, headers=json.loads(self.headers) if len(self.headers) != 0 else {},
                                json=json.loads(self.body))
        return response

    def delete(self):
        response = requests.delete(self.url)
        return response


app = QApplication([])
app.setWindowIcon(QIcon('static/img/logo.jpg'))
stats = Index()
stats.ui.show()
app.exec_()
