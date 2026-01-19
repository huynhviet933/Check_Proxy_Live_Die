import requests
import threading
from concurrent.futures import ThreadPoolExecutor
import os

# --- CẤU HÌNH ---
INPUT_FILE = "proxies.txt"
TIMEOUT = 15
THREADS = 50 

file_lock = threading.Lock()

def save_result(filename, proxy_str):
    with file_lock:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{proxy_str}\n")

def parse_proxy(proxy_str):
    """
    Chuyển đổi các định dạng proxy về dạng chuẩn để thư viện requests có thể hiểu được.
    """
    proxy_str = proxy_str.strip()
    
    # Dạng 1: Đã có giao thức http:// hoặc https://
    if proxy_str.startswith(("http://", "https://")):
        return proxy_str
    
    # Dạng 2: IP:PORT:USER:PASS hoặc IP:PORT
    parts = proxy_str.split(':')
    
    if len(parts) == 4:
        # IP:PORT:USER:PASS -> http://user:pass@ip:port
        ip, port, user, pw = parts
        return f"http://{user}:{pw}@{ip}:{port}"
    
    elif len(parts) == 2:
        # IP:PORT -> http://ip:port
        return f"http://{proxy_str}"
    
    # Trường hợp khác (ví dụ user:pass@ip:port nhưng thiếu http)
    return f"http://{proxy_str}"

def check_proxy(raw_proxy):
    if not raw_proxy.strip():
        return

    # Chuyển đổi để Requests có thể chạy được
    formatted_proxy = parse_proxy(raw_proxy)
    
    proxies = {
        "http": formatted_proxy,
        "https": formatted_proxy
    }

    try:
        # Kiểm tra qua API ip-api
        response = requests.get(
            "http://ip-api.com/json/", 
            proxies=proxies, 
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                country_code = data.get("countryCode") # Ví dụ: VN, US, DE
                
                print(f"[LIVE] {raw_proxy} -> {country_code}")
                
                # Lưu kết quả bằng raw_proxy (định dạng gốc)
                save_result("live.txt", raw_proxy)
                save_result(f"{country_code}.txt", raw_proxy)
            else:
                print(f"[LIVE-ERR] {raw_proxy} (Không xác định được vị trí)")
                save_result("live.txt", raw_proxy)
        else:
            print(f"[DIE] {raw_proxy} (Status: {response.status_code})")
            save_result("die.txt", raw_proxy)
            
    except Exception:
        print(f"[DIE] {raw_proxy}")
        save_result("die.txt", raw_proxy)

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Lỗi: Không tìm thấy file {INPUT_FILE}!")
        return

    # Đọc toàn bộ proxy vào list
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        proxy_list = [line.strip() for line in f if line.strip()]

    print(f"Đã nạp {len(proxy_list)} proxy. Đang kiểm tra...")
    print("-" * 50)

    # Sử dụng ThreadPool để tăng tốc độ
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        executor.map(check_proxy, proxy_list)

    print("-" * 50)
    print("HOÀN THÀNH!")

if __name__ == "__main__":
    main()
