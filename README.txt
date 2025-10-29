System/
│
├── app/                             # Ứng dụng desktop PyQt5
│   ├── main.py                      # File chạy chính của app
│   ├── plc_client.py                # Class giao tiếp PLC
│   ├── ui_mainwindow.py             # File giao diện sinh ra từ Qt Designer (nếu dùng)
│   ├── widgets.py                   # Các widget custom (nếu có)
│   ├── resources/                   # Ảnh, icon, file .ui, ...
│   │   └── mainwindow.ui
│   └── utils.py                     # Hàm tiện ích dùng chung cho app
│
├── webserver/                       # Webserver FastAPI
│   ├── main.py                      # File chạy chính của webserver
│   ├── plc_client.py                # Class giao tiếp PLC (dùng chung hoặc copy từ app)
│   ├── routes.py                    # Định nghĩa các API endpoint
│   ├── static/                      # Thư mục chứa file tĩnh (JS, CSS, ảnh)
│   │   ├── app.js
│   │   └── style.css
│   ├── templates/                   # Thư mục chứa file HTML (Jinja2)
│   │   └── index.html
│   └── utils.py                     # Hàm tiện ích dùng chung cho webserver
│
├── shared/                          # Thư viện dùng chung (nếu muốn)
│   └── plc_client.py                # Class PLCClient dùng chung cho cả app và webserver
│
├── requirements.txt                 # Danh sách thư viện Python cần cài
├── README.md                        # Hướng dẫn sử dụng dự án
└── .gitignore                       # Các file/thư mục không đưa lên git

------------------------------------------------------------------------------------------------------------------

app/main.py: Khởi tạo và chạy ứng dụng PyQt5.

app/plc_client.py: Class giao tiếp PLC (có thể dùng chung với webserver).

app/ui_mainwindow.py: File giao diện sinh ra từ Qt Designer (pyuic5).

app/widgets.py: Các widget custom nếu bạn mở rộng giao diện.

app/resources/: Chứa file .ui, icon, ảnh...

app/utils.py: Các hàm tiện ích cho app.

webserver/main.py: Khởi tạo và chạy FastAPI.

webserver/plc_client.py: Class giao tiếp PLC (dùng chung hoặc copy từ app).

webserver/routes.py: Định nghĩa các API endpoint (status, điều khiển PLC...).

webserver/static/: Chứa JS, CSS, ảnh cho giao diện web.

webserver/templates/: Chứa file HTML (dùng Jinja2 hoặc FastAPI).

webserver/utils.py: Các hàm tiện ích cho webserver.

shared/plc_client.py: Nếu muốn dùng chung class PLCClient cho cả app và webserver, đặt ở đây và import vào hai nơi.

requirements.txt:


------------------------------------------------------------------------------------------------------------------

Nguyen lý dieu khiển hệ thống: 

App giao diện:
	Đọc/ghi PLC
	Mở socket server nhận lệnh điều khiển từ webserver
	Gửi trạng thái PLC về cho webserver khi được yêu cầu
	Hiển thị trạng thái lên giao diện
Webserver:
	Gửi lệnh điều khiển tới app giao diện qua socket
	Đọc trạng thái từ app giao diện qua socket
	Cung cấp API cho frontend
Frontend:
	Gửi lệnh điều khiển qua API
	Hiển thị trạng thái realtime
------------------------------------------------------------------------------------------------------------------
Bước làm từng bước từng phần qua trinh thuc hien: 

APP giao diện:  App tao giao dien qt_designer5
	Khi tao giao dien tren app xong --> luu ve lap (file.ui) ---> chuyen qua (file.py) bang lenh(cd vi tri file.ui/pyuic5.exe -x mainwindow.ui -o ui_mainwindow.py)
	dat ten QBUTTON, QLABEL... de nhan lenh dieu khien tu main.py qua cac thu vien (import sys
											import time
											import threading
											import socket
											import json
											from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
											from PyQt5.QtCore import QTimer
											from ui_mainwindow import Ui_MainWindow  # File sinh ra từ Qt Designer) 
WEBSERVER: 
	FRONEND(.JS, .CSS, HTML):
	BACKEND: (main.py, route.py)

			Thuật toán: Chức năng: Khi khách hàng truy cập vào trang web --> Tiến đến chọn sản phẩm là giấy
			--> web có các lựa chọn để tích vào 1 hay 2 loại giấy với 2 loại chiều dài mặc định là 6cm và 8cm--> chọn
			số lượng giấy cho mỗi loại chiều dài (ví dụ: mặc định là 10 và có dấu + - để tăng giảm số lượng là 
			bội số của 10 với 2 loại chiều dài 6 và 8 tương ứng) --> nếu tổng số lượng khách hàng chọn là giấy 6cm hoặc/và 8cm <=20 thì web tự tạo ra 1 mã qr tương
			ứng sắp xếp ưu tiên 6cm trước và 8cm sau, nếu số lượng lớn hơn 20(ví dụ: 19 là 6cm và 11 là 8cm thì tạo ra 2 mã qr
			: 1 mã có số lượng 19 6cm và 1 8cm, mã qr còn lại là loại 8cm số lượng 10, tương ứng với các đơn hàng tiếp theo lớn hơn 20 vì thùng chỉ 
			chứa tối đa 20 sản phẩm)
			- Sau khi tạo mã Qr --> lưu dữ liệu vào bảng tính ggsheet bao gồm các thông tin sau: ID,đơn hàng số, loại giấy,
			số lượng mỗi loại, thời gian,các mã qr của đơn hàng đó(nếu tổng số lượng <=20: 1 mã, >20 thì số lượng mã qr tương ứng)

	Lưu dữ liệu ggsheet:
				1. Tạo file key Google API (service_account.json)
			A. Tạo Google Cloud Project & bật Google Sheets API

			Truy cập: https://console.cloud.google.com/
			Tạo Project mới (hoặc chọn project bạn muốn dùng).
			Vào “APIs & Services” → “Enable APIs and Services”.
			Tìm “Google Sheets API” và “Google Drive API”, nhấn “Enable” cho cả 2.
			B. Tạo Service Account & tải file key

			Vào “APIs & Services” → “Credentials”.
			Nhấn “Create Credentials” → “Service account”.
			Đặt tên, nhấn “Create and Continue” (có thể bỏ qua các bước phân quyền).
			Sau khi tạo xong, chọn service account vừa tạo → “Keys” → “Add Key” → “Create new key” → chọn “JSON” → “Create”.
			File service_account.json sẽ được tải về. Đặt file này vào thư mục webserver của dự án.
			C. Chia sẻ Google Sheet cho service account

			Mở file service_account.json, tìm trường "client_email", ví dụ:
			"client_email": "abc-xyz@your-project.iam.gserviceaccount.com"
			Mở Google Sheet bạn muốn ghi, nhấn “Chia sẻ” (Share), dán email trên vào, cấp quyền Editor.
			2. Lấy Google Sheet ID
			Mở Google Sheet trên trình duyệt, link dạng:
			https://docs.google.com/spreadsheets/d/1AbCDEFGHIJKL1234567890abcdefgHIJKL/edit#gid=0
			Sheet ID là phần nằm giữa /d/ và /edit, ví dụ:
			1AbCDEFGHIJKL1234567890abcdefgHIJKL
			3. Cập nhật code
			Đặt file service_account.json vào đúng thư mục.
			Thay YOUR_SHEET_ID trong code bằng Sheet ID bạn vừa lấy.
			Đảm bảo tên sheet (worksheet) đúng, ví dụ "Sheet1".
	Tạo tài khoản đăng nhập webserver:
		Thuật toán: mỗi khi truy cập địa chỉ web thì yêu cầu tài khoản/mật khẩu/mã xác thực do admin cung cấp
		( 1 cái chỉ xem, 1 cái cho điều khiển): nếu không có tài khoản thì có nút tạo tài khoản(bao gồm 2 thông tin: tài khoản/ mật khẩu)
		--> sau khi tạo tài khoản xong thì web tự quay lại trang đăng nhập. Quyền chỉ xem là chỉ được tạo đơn hàng và đặt hàng(còn lại khi nhấn nút 
		điều khiển sẽ thông báo: bạn không có quyền điều khiển hệ thống) còn quyền điều khiển thì cho làm tất cả tác vụ.

NGROK APP FREE: 
	LINK WEB: https://dashboard.ngrok.com/get-started/your-authtoken
	LINK API: 2ycimC6D6HnqlBhe86TKv4bXzdt_ftAmiVwWbkRqTmm9xbpV
	Trước khi dung lệnh: mở NGrok.exe
	LỆNH TẠO WEB command ngrok: ngrok config add-authtoken 2ycimC6D6HnqlBhe86TKv4bXzdt_ftAmiVwWbkRqTmm9xbpV
	Lệnh ONLINE NGROK GLOBAL: ngrok http 8000
	coppy link : forwarding : dạng : "https:// MÃ.ngrok-free.app"

xu ly anh: 
Thuật toán: chia khung hình camera thành 3 vùng nhận diện: vùng trong đường line màu đỏ là vùng miệng thùng, vùng trong đường line màu vàng là vùng phát hiện giấy mới và vùng còn lại là vùng phát hiện giấy lỗi rơi ra khỏi vùng thùng.
Nguyên lý detect:Loại bỏ nhận diện vùng trong miệng thùng(đường line hình vuông màu đỏ)  Khi phát hiện trong khung hình có 2 class(paper, box) thì bắt đầu nhận diện phát hiện lỗi  xác định đường line màu xanh lá cây  phát hiện giấy mới nằm trong vùng màu vàng xác nhận tọa độ vị trí điểm đầu giấy: nếu điểm đầu giấy(điểm màu xanh dương đậm) vượt qua đường line màu xanh lá cây thì bắt đầu đếm một khoảng thời gian 0.5s  nếu sau khoảng thời gian này  phát hiện giấy nằm trong vùng còn lại(vùng ngoài màu vàng và màu đỏ) thì xác nhận lỗi giấy rơi ra khỏi vùng miệng thùng chứa, ngược lại thì giấy đã rơi vào thùng đúng.














































