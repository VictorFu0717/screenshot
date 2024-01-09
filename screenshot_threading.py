import glob
import os
import csv
import traceback
import time
import datetime as dt

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
import threading
import encodings.idna
# encodings.idna沒有這行打包時編碼會出問題

file_lock = threading.RLock()

def http_list(file_path,thread_num=10):
    # 供10個線程使用

    temp_list = []
    output = []
    pdf_list = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        # 跳过表头行
        next(reader)

        # 逐行读取数据
        for row in reader:
            url = row[0]
            if '.pdf' in url:
                if row not in pdf_list:
                    pdf_list.append(row)
            else:
                if row not in temp_list: # 網址是pdf格式的無法截圖,因此篩選掉
                # row 是一个列表，包含 CSV 文件的一行数据
                    temp_list.append(row)


    lens = len(temp_list)
    batch = lens//thread_num+1
    print('lens:',lens)

    for i in range(thread_num):
        start = i * batch
        end = min((i + 1) * batch, lens)

        http_list_dict = {}
        for j in range(start, end):
            # http_list_dict[temp_list[j]] = f'{j}.png'
            http_list_dict[f'{j}.png'] = temp_list[j]

        output.append(http_list_dict)
        # output = [{"網址0":"0.png", "網址1":"1.png", "網址2":"2.png"}, {"網址3":"3.png"...}...]
        # output = [{batch_0}, {batch_1}....]

    # n = 0
    # for i in temp_list:
    #     http_list_dict[i] = f'{n}.png'
    #     n += 1
    print(f'output:{output}')
    return output, pdf_list


def start(http_list_dict, start_time):

    # 打印"開始搜尋"
    print(dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S  ") + "進程 " + str(os.getpid()) + " 開始搜尋 " )

    # 開啟chromedriver
    # d = DesiredCapabilities.CHROME
    # d["loggingPrefs"] = {"browser": "ALL"}
    # 利用Service避免延遲造成chromedriver沒有完全關閉
    Chrome_Service = Service("chromedriver.exe")
    Chrome_Service.command_line_args()
    Chrome_Service.start()
    chrome_options = Options()  # 如果這裡寫 chrome_options = Chromeoption() 會跳出DeprecationWarning: use options instead of chrome_options。因此改用Options
    chrome_options.add_argument("--headless")  # 使用無頭模式
    chrome_options.add_argument("--disable-gpu")  # 如果不加這個選項，有時定位會出現問題(根據網路上的說法，用來規避google的bug)
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽視https certificate error
    chrome_options.add_argument('--no-sandbox') # 以最高權限運行
    chrome_options.add_argument('window-size=1920x1080')
    # chrome_options.add_argument('window-size=2000x2000')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36")  # 加入user agent變得更像人
    chrome_options.add_argument("--dns-prefetch-disable")  # 用來避免timeout renderer
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])  # 避免 chromedriver 一直打印log訊息
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)  # 設置三十秒鐘加載時間
    driver.implicitly_wait(30)
    request_headers = {'user-agent': '"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}


    for pic_name, info in http_list_dict.items():

        # r = requests.get(i, headers=request_headers, timeout=5)
        # status = r.status_code
        # print(status,type(status))
        # if status == 200:
        http = info[0]
        topic = info[1]
        DN = info[2]
        try :
            driver.get(http)
            time.sleep(2)
            # 模拟按下 Page Down 键
            element = driver.find_element(By.TAG_NAME,"body")
            # element.send_keys(Keys.PAGE_DOWN)
            # 执行 JavaScript 模拟滚动
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            height = driver.execute_script("return document.documentElement.scrollHeight")
            if height > 2350:
                height = 2350
            driver.set_window_size(1920,height)
            time.sleep(2)
            driver.get_screenshot_as_file(f'output_screenshot/screenshot_picture_{start_time}//{pic_name}')
            with file_lock:
                with open(f"output_screenshot/screenshot_picture_{start_time}\\" + "\\mapping_list" + ".txt", mode="a",
                          encoding="utf-8") as f:
                    f.write(f'{pic_name}, {http}, {topic}, {DN}' + '\n')
        except WebDriverException as e:


            print(dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S  "))
            print("出現錯誤")
            print(traceback.format_exc())
            with file_lock:
                with open(f"output_screenshot/screenshot_picture_{start_time}\\" + "\\Exceptions_" + ".txt", mode="a",
                          encoding="utf-8") as file:
                    # file.write(dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S  ") + "\n")
                    # file.write(" 出現錯誤" + "\n")
                    file.write(http + "\n")
                    # file.write("\n\n")
                    # os.system("pause")

            continue

    driver.quit()
    Chrome_Service.stop()




# 主程式
if __name__ == "__main__":
    # 開幾個線程
    thread_num = 10

    # file_path = 'IWIN案_8月檢索總數_20230804.csv'
    file_path = glob.glob('.\input_screenshot\*.csv')[0]
    print(file_path)

    start_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    http_list_, pdf_list = http_list(file_path,thread_num)
    print(len(http_list_))
    threads = []
    if not os.path.exists("output_screenshot"):
        os.mkdir("output_screenshot")

    if not os.path.exists(f"output_screenshot/screenshot_picture_{start_time}"):
        os.mkdir(f"output_screenshot/screenshot_picture_{start_time}")

    # wirte pdf list
    with open(f"output_screenshot/screenshot_picture_{start_time}\\" + "\\pdf_list" + ".txt", mode="a",
              encoding="utf-8") as f:
        f.write('URL, 標題, DN' + "\n")
        for pdf in pdf_list:
            f.write(f'{pdf[0]}, {pdf[1]}, {pdf[2]}' + "\n")

    # write mapping list's title
    with open(f"output_screenshot/screenshot_picture_{start_time}\\" + "\\mapping_list" + ".txt", mode="a",
              encoding="utf-8") as f:
        f.write('ID, URL, 標題, DN' + "\n")
    for i in range(thread_num):
        http_list_dict = http_list_[i]
        threads.append(threading.Thread(target=start, args=(http_list_dict, start_time,)))
        threads[i].start()

    # 等待所有子執行緒結束
    for i in range(thread_num):
        threads[i].join()

    print("Done!")