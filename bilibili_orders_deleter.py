import requests
import json
import time
import sys
import os
import re
from typing import List, Dict, Any
try:
    import keyboard
except ImportError:
    keyboard = None

def get_version():
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        version_file = os.path.join(base_path, "version_info.txt")
        
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r"StringStruct\(u'ProductVersion',\s*u'([^']+)'\)", content)
                if match:
                    return match.group(1)
        
        return "0.0.0"
    except Exception as e:
        return "未知版本"

def show_muse_banner():
    banner = r"""
          _____                    _____                    _____                    _____          
         /\    \                  /\    \                  /\    \                  /\    \         
        /::\____\                /::\____\                /::\    \                /::\    \        
       /::::|   |               /:::/    /               /::::\    \              /::::\    \       
      /:::::|   |              /:::/    /               /::::::\    \            /::::::\    \      
     /::::::|   |             /:::/    /               /:::/\:::\    \          /:::/\:::\    \     
    /:::/|::|   |            /:::/    /               /:::/__\:::\    \        /:::/__\:::\    \    
   /:::/ |::|   |           /:::/    /                \:::\   \:::\    \      /::::\   \:::\    \   
  /:::/  |::|___|______    /:::/    /      _____    ___\:::\   \:::\    \    /::::::\   \:::\    \  
 /:::/   |::::::::\    \  /:::/____/      /\    \  /\   \:::\   \:::\    \  /:::/\:::\   \:::\    \ 
/:::/    |:::::::::\____\|:::|    /      /::\____\/::\   \:::\   \:::\____\/:::/__\:::\   \:::\____\
\::/    / ~~~~~/:::/    /|:::|____\     /:::/    /\:::\   \:::\   \::/    /\:::\   \:::\   \::/    /
 \/____/      /:::/    /  \:::\    \   /:::/    /  \:::\   \:::\   \/____/  \:::\   \:::\   \/____/ 
             /:::/    /    \:::\    \ /:::/    /    \:::\   \:::\    \       \:::\   \:::\    \     
            /:::/    /      \:::\    /:::/    /      \:::\   \:::\____\       \:::\   \:::\____\    
           /:::/    /        \:::\__/:::/    /        \:::\  /:::/    /        \:::\   \::/    /    
          /:::/    /          \::::::::/    /          \:::\/:::/    /          \:::\   \/____/     
         /:::/    /            \::::::/    /            \::::::/    /            \:::\    \         
        /:::/    /              \::::/    /              \::::/    /              \:::\____\        
        \::/    /                \::/____/                \::/    /                \::/    /        
         \/____/                  ~~                       \/____/                  \/____/                                                                                                        
    """
    print(banner)
    version = get_version()
    print(f"MUSE-BiliOrders-Deleter v{version}")
    print("=" * 88)
    print()

class BiliBiliOrdersDeleter:
    def __init__(self):
        self.session = requests.Session()
        self.cookies = ""
        self.orders = []
        
    def set_cookies(self, cookies: str):
        self.cookies = cookies
        if cookies:
            cookie_dict = {}
            for item in cookies.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookie_dict[key] = value
            self.session.cookies.update(cookie_dict)
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://show.bilibili.com/',
            'Origin': 'https://show.bilibili.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def fetch_all_orders(self, page_size: int = 20) -> bool:
        page_num = 0
        total_orders = 0
        
        print("正在获取订单列表...")
        
        while True:
            url = f"https://show.bilibili.com/api/ticket/ordercenter/list?pageNum={page_num}&pageSize={page_size}"
            
            try:
                response = self.session.get(url, headers=self.get_headers())
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('code') != 0:
                    print(f"获取订单失败: {data.get('message', '未知错误')}")
                    if 'data' in locals():
                        print(f"服务器返回详情: {data}")
                    return False
                
                orders_data = data.get('data', {}).get('list', [])
                total_count = data.get('data', {}).get('total', 0)
                
                if not orders_data:
                    break
                
                self.orders.extend(orders_data)
                total_orders += len(orders_data)
                
                print(f"第{page_num + 1}页: 获取到 {len(orders_data)} 个订单")
                
                if len(orders_data) < page_size or total_orders >= total_count:
                    break
                
                page_num += 1
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"网络请求错误: {e}")
                return False
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                return False
        
        print(f"✓ 总共获取到 {total_orders} 个订单")
        return True
    
    def display_orders_interactive(self) -> List[int]:
        if not self.orders:
            print("没有找到订单")
            return []
        
        if keyboard is None:
            print("错误: keyboard库未安装，程序无法运行")
            print("请运行: pip install keyboard")
            return []
        
        selected = [False] * len(self.orders)
        current_index = 0
        
        def clear_screen():
            os.system('cls' if os.name == 'nt' else 'clear')
        
        def display_current_page():
            print(f"=== B站会员购订单删除器 ===")
            print(f"总共 {len(self.orders)} 个订单")
            print(f"使用 ↑↓ 键移动，空格键选择/取消选择，Enter确认，ESC退出")
            print("\n" + "═" * 100)
            
            print(f"{'选择':<6} {'序号':<6} {'订单名':<60} {'订单号':<18} {'状态':<10} {'创建时间':<12}")
            print("─" * 112)
            
            start_idx = max(0, current_index - 10)
            end_idx = min(len(self.orders), start_idx + 20)
            
            for i in range(start_idx, end_idx):
                order = self.orders[i]
                rows = order.get('rows', [])
                if rows:
                    activity_name = rows[0].get('name', '未知订单')
                else:
                    activity_name = '未知订单'
                
                if len(activity_name.encode('utf-8')) > 58:
                    truncated = ""
                    byte_count = 0
                    for char in activity_name:
                        char_bytes = len(char.encode('utf-8'))
                        if byte_count + char_bytes > 55:
                            truncated += "..."
                            break
                        truncated += char
                        byte_count += char_bytes
                    activity_name = truncated
                
                order_id = str(order.get('order_id', '未知订单号'))
                status = order.get('status_name', '') or order.get('status_subname', '') or '未知状态'
                if len(status.encode('utf-8')) > 10:
                    truncated = ""
                    byte_count = 0
                    for char in status:
                        char_bytes = len(char.encode('utf-8'))
                        if byte_count + char_bytes > 7:
                            truncated += "..."
                            break
                        truncated += char
                        byte_count += char_bytes
                    status = truncated
                

                order_ctime = order.get('order_ctime', 0)
                if order_ctime:
                    import datetime
                    create_time = datetime.datetime.fromtimestamp(order_ctime).strftime('%Y-%m-%d')
                else:
                    create_time = '未知'
                

                check_text = "[✓]" if selected[i] else "[ ]"
                

                if i == current_index:
                    prefix = "► "
                else:
                    prefix = "  "
                

                line = f"{prefix}{check_text:<4} {i+1:<6} {activity_name:<60} {order_id:<18} {status:<10} {create_time:<12}"
                
                print(line)
            
            if end_idx < len(self.orders):
                print(f"... 还有 {len(self.orders) - end_idx} 个订单")
            
            print("─" * 100)
            selected_count = sum(selected)
            print(f"已选择: {selected_count} 个订单")
        
        print('\033[H\033[J', end='')
        display_current_page()
        
        while True:
            try:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    need_refresh = False
                    
                    if event.name == 'up':
                        if current_index > 0:
                            current_index -= 1
                            need_refresh = True
                    elif event.name == 'down':
                        if current_index < len(self.orders) - 1:
                            current_index += 1
                            need_refresh = True
                    elif event.name == 'space':
                        selected[current_index] = not selected[current_index]
                        need_refresh = True
                    elif event.name == 'enter':
                        break
                    elif event.name == 'esc':
                        return []
                    elif event.name == 'a':
                        selected = [True] * len(self.orders)
                        need_refresh = True
                    elif event.name == 'c':
                        selected = [False] * len(self.orders)
                        need_refresh = True
                    
                    if need_refresh:
                        time.sleep(0.1)
                        print('\033[H\033[J', end='')
                        display_current_page()
                        
            except KeyboardInterrupt:
                return []
        
        return [i for i, sel in enumerate(selected) if sel]
    
    def delete_order(self, order_id: str, order_data: Dict[str, Any] = None) -> bool:
        if order_data and order_data.get('order_type') == 9:
            print(f"✗ 工房订单 {order_id} 删除失败: 暂不支持删除工房订单，请手动删除")
            return False
        
        is_mall_order = self.is_mall_order(order_data) if order_data else False
        
        if is_mall_order:
            url = f"https://mall.bilibili.com/mall-c/order/delete?orderId={order_id}"
            headers = self.get_headers()
            
            try:
                response = self.session.get(url, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get('code') == 0:
                    print(f"✓ 商品订单 {order_id} 删除成功")
                    return True
                else:
                    error_msg = result.get('msg', '未知错误')
                    error_code = result.get('errno', 'N/A')
                    print(f"✗ 商品订单 {order_id} 删除失败: {error_msg}")
                    print(f"   错误代码: {error_code}")
                    print(f"   完整响应: {result}")
                    return False
                    
            except requests.RequestException as e:
                print(f"✗ 删除商品订单 {order_id} 时网络错误: {e}")
                return False
            except json.JSONDecodeError as e:
                if response.status_code == 200 and not response.text.strip():
                    print(f"✓ 商品订单 {order_id} 删除成功 (响应为空但状态码正常)")
                    return True
                else:
                    print(f"✗ 删除商品订单 {order_id} 时JSON解析错误: {e}")
                    print(f"   响应状态码: {response.status_code}")
                    print(f"   响应内容: {response.text[:200]}..." if len(response.text) > 200 else f"   响应内容: {response.text}")
                    return False
        else:
            url = "https://show.bilibili.com/api/ticket/order/del"
            
            data = {
                'order_id': order_id,
                'csrf': self.session.cookies.get('bili_jct', '')
            }
            
            headers = self.get_headers()
            headers['Content-Type'] = 'application/json'
            
            try:
                response = self.session.post(url, json=data, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get('code') == 0 or result.get('errno') == 0:
                    print(f"✓ 活动订单 {order_id} 删除成功")
                    return True
                else:
                    error_msg = result.get('msg', '未知错误')
                    error_code = result.get('errno') or result.get('code', 'N/A')
                    print(f"✗ 活动订单 {order_id} 删除失败: {error_msg}")
                    print(f"   错误代码: {error_code}")
                    print(f"   完整响应: {result}")
                    return False
                    
            except requests.RequestException as e:
                print(f"✗ 删除活动订单 {order_id} 时网络错误: {e}")
                return False
            except json.JSONDecodeError as e:
                if response.status_code == 200 and not response.text.strip():
                    print(f"✓ 活动订单 {order_id} 删除成功 (响应为空但状态码正常)")
                    return True
                else:
                    print(f"✗ 删除活动订单 {order_id} 时JSON解析错误: {e}")
                    print(f"   响应状态码: {response.status_code}")
                    print(f"   响应内容: {response.text[:200]}..." if len(response.text) > 200 else f"   响应内容: {response.text}")
                    return False
    
    def is_mall_order(self, order_data: Dict[str, Any]) -> bool:
        if not order_data:
            return False
        order_type = order_data.get('order_type', 1)
        return order_type == 2
    
    def delete_selected_orders(self, indices: List[int]):
        if not indices:
            return
        
        print(f"\n准备删除 {len(indices)} 个订单...")
        
        success_count = 0
        fail_count = 0
        
        for i, index in enumerate(indices, 1):
            order = self.orders[index]
            order_id = str(order.get('order_id'))
            rows = order.get('rows', [])
            if rows:
                activity_name = rows[0].get('name', '未知订单')
            else:
                activity_name = '未知订单'
            
            print(f"[{i}/{len(indices)}] 正在删除订单: {activity_name} ({order_id})")
            
            if self.delete_order(order_id, order):
                success_count += 1
            else:
                fail_count += 1
            

            if i < len(indices):
                time.sleep(1)
        
        print(f"\n删除完成！成功: {success_count}, 失败: {fail_count}")
    
    def run(self):
        show_muse_banner()
        print(f"⚠️注意：请确保您有权限删除这些订单，删除操作不可恢复！")
        print(f"提示：若订单列表显示换行请尝试将窗口拉宽")
        

        cookies = input("\n请输入您的B站cookies: ").strip()
        if not cookies:
            print("cookies不能为空")
            return
        
        self.set_cookies(cookies)
        

        if not self.fetch_all_orders():
            print("获取订单失败，请检查cookies是否正确")
            return
        
        if not self.orders:
            print("没有找到任何订单")
            return
        

        indices = self.display_orders_interactive()
        
        if not indices:
            print("未选择任何订单，程序退出")
            return
        

        selected_orders = [self.orders[i] for i in indices]
        print(f"\n您选择删除以下 {len(selected_orders)} 个订单:")
        for order in selected_orders:
            rows = order.get('rows', [])
            if rows:
                activity_name = rows[0].get('name', '未知订单')
            else:
                activity_name = '未知订单'
            order_id = str(order.get('order_id', '未知订单号'))
            status = order.get('status_name', '') or order.get('status_subname', '') or '未知状态'
            print(f"- {activity_name} ({order_id}) - {status}")
        
        if keyboard is not None:
            try:
                while keyboard.is_pressed('enter') or keyboard.is_pressed('space') or keyboard.is_pressed('up') or keyboard.is_pressed('down'):
                    time.sleep(0.01)
            except Exception as e:
                 import traceback
                 print(f"删除订单时发生未知错误: {e}")
                 print("完整错误详情:")
                 print(traceback.format_exc())
        

        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except ImportError:
            pass
        
        print("\n确认删除这些订单吗？(Y/N): ", end='', flush=True)
        confirm = input().strip().lower()
        if confirm != 'y':
            print("操作已取消")

            return
        

        self.delete_selected_orders(indices)

def main():
    while True:
        try:
            deleter = BiliBiliOrdersDeleter()
            deleter.run()
        except KeyboardInterrupt:
            print("\n程序已被用户中断")
        except Exception as e:
            import traceback
            print(f"程序运行出错: {e}")
            print("\n完整错误详情:")
            print(traceback.format_exc())
        
        while True:
            choice = input("\n退出(T)/重新开始(S): ").strip().upper()
            if choice == 'T':
                print("程序已退出")
                return
            elif choice == 'S':
                print("\n重新开始程序...\n")
                break
            else:
                print("请输入 T 或 S")

if __name__ == "__main__":
    main()