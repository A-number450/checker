import os
import requests
from flask import Flask, render_template, request
from PIL import Image

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = []
    if request.method == 'POST':
        image = request.files['image']
        user_text = request.form['text']

        # 將圖片儲存為暫存檔案
        image_path = "temp.png"
        image.save(image_path)

        # 上傳至 ocr.space API 辨識文字
        api_key = "helloworld"  # 免費帳號 API key
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://api.ocr.space/parse/image",
                files={"filename": f},
                data={"apikey": api_key, "language": "cht"}
            )
        os.remove(image_path)  # 刪掉暫存圖片

        try:
            ocr_result = r.json()['ParsedResults'][0]['ParsedText']
        except Exception:
            ocr_result = ""

        # 從圖片文字中擷取代碼與數量
        image_items = {}
        for line in ocr_result.split('\n'):
            if 'BA' in line:
                parts = line.strip().split()
                code = None
                quantity = None
                for p in parts:
                    if 'BA' in p:
                        code = p.strip('[]():')
                for p in reversed(parts):
                    if p.isdigit():
                        quantity = int(p)
                        break
                if code and quantity is not None:
                    image_items[code] = quantity

        # 從使用者貼上的文字擷取代碼與數量
        text_items = {}
        for line in user_text.split('\n'):
            if 'BA' in line:
                parts = line.strip().split()
                code = parts[0]
                for word in parts:
                    if '每月' in word:
                        digits = ''.join(filter(str.isdigit, word))
                        if digits:
                            text_items[code] = int(digits)

        # 比對兩邊的數字
        for code in image_items:
            expected = image_items.get(code)
            typed = text_items.get(code, 0)
            result.append({
                'code': code,
                'expected': expected,
                'typed': typed,
                'match': expected == typed
            })

    return render_template('index.html', result=result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
