from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import requests
import json
import csv
import io
import time
import logging
from datetime import datetime
import re
import urllib.parse
from tplinkrouterc6u import TplinkRouterProvider, AbstractRouter, Firmware, Status, Connection, LTEStatus

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TPLinkManager:
    def __init__(self):
        self.router = None
        self.logger = logging.getLogger(__name__)
        self.pushplus_token = os.environ.get('PUSHPLUS_TOKEN', None)
        self.devices_file = '/app/data/known_devices.json'  # 持久化设备记录文件
        self.previous_devices = self._load_known_devices()  # 存储之前已知的设备，用于检测新设备

    def login(self, host, password):
        """登录路由器 - 使用与HA集成相同的方式"""
        try:
            # 标准化主机地址
            if not host.startswith('http'):
                host = f'http://{host}'

            # 使用与HA集成相同的获取客户端方法
            self.router = TplinkRouterProvider.get_client(
                host=host,
                password=password,
                username="admin",  # HA集成中的默认用户名
                logger=self.logger,
                verify_ssl=False
            )

            # 测试连接
            self.router.authorize()

            # 获取路由器信息以验证连接
            firmware = self.router.get_firmware()
            status = self.router.get_status()

            self.logger.info(f"成功连接到路由器: {firmware.model}")

            return True

        except Exception as e:
            raise Exception(f"登录失败: {str(e)}")

    def get_devices(self):
        """获取连接的设备列表 - 使用与HA集成相同的方式"""
        if not self.router:
            raise Exception("未登录，请先登录")

        try:
            # 使用与HA集成相同的方式获取状态
            status = self.router.get_status()

            # 解析设备信息
            devices = []
            for device in status.devices:
                # 将MAC地址格式从 xx-xx-xx-xx-xx-xx 转换为 xx:xx:xx:xx:xx:xx
                mac_address = device.macaddr.replace('-', ':')
                devices.append({
                    'mac_address': mac_address,
                    'name': device.hostname if device.hostname else mac_address,
                    'ip_address': device.ipaddr,
                    'connection_type': device.type.get_type() if hasattr(device.type, 'get_type') else str(device.type),
                    'active': device.active,
                    'down_speed': getattr(device, 'down_speed', None),
                    'up_speed': getattr(device, 'up_speed', None),
                    'packets_sent': getattr(device, 'packets_sent', None),
                    'packets_received': getattr(device, 'packets_received', None)
                })

            return devices

        except Exception as e:
            raise Exception(f"获取设备列表失败: {str(e)}")

    def _load_known_devices(self):
        """从文件加载已知的设备记录"""
        try:
            import json
            if os.path.exists(self.devices_file):
                with open(self.devices_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"加载已知设备记录失败: {str(e)}")
        return {}

    def _save_known_devices(self):
        """保存已知设备记录到文件"""
        try:
            import json
            with open(self.devices_file, 'w', encoding='utf-8') as f:
                json.dump(self.previous_devices, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存已知设备记录失败: {str(e)}")

    def check_and_notify_new_devices(self, current_devices):
        """检查新设备并发送通知"""
        if not self.pushplus_token:
            return False

        # 检查是否有真正的新设备
        new_devices = []
        for device in current_devices:
            mac_address = device['mac_address']
            device_name = device['name']

            # 只有两种情况会触发通知：
            # 1. 设备MAC地址从未被记录过（全新设备）
            # 2. 设备名称仍然是MAC地址（未命名的设备）
            if (mac_address not in self.previous_devices or
                self.previous_devices[mac_address] == mac_address):
                new_devices.append(device)

        if new_devices:
            # 更新已知设备列表（保存最新的设备名称）
            for device in current_devices:
                self.previous_devices[device['mac_address']] = device['name']

            # 保存到文件
            self._save_known_devices()

            # 发送通知
            self._send_pushplus_notification(new_devices)
            return True

        return False

    def _send_pushplus_notification(self, new_devices):
        """发送 PushPlus 通知"""
        try:
            # 构建通知内容
            title = "有新的设备连接到家庭网络了"

            # 生成设备信息HTML
            devices_html = ""
            for device in new_devices:
                device_name = device['name']
                ip_address = device['ip_address']
                mac_address = device['mac_address']

                devices_html += f"""
                <div style="margin: 10px 0; padding: 10px; border: 1px solid #eee; border-radius: 5px;">
                    <strong>设备名称:</strong> {device_name}<br>
                    <strong>IP地址:</strong> {ip_address}<br>
                    <strong>MAC地址:</strong> {mac_address}
                </div>
                """

            content = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h3 style="color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                    检测到新设备连接
                </h3>
                <p style="color: #666; margin-bottom: 20px;">
                    <strong>请注意：</strong>以下设备是首次连接到家庭网络，请及时固定IP地址并修改设备名称。
                </p>
                {devices_html}
                <p style="color: #888; font-size: 12px; margin-top: 20px;">
                    -- TP-Link Device Manager 自动通知 --
                </p>
            </div>
            """

            # 发送 PushPlus 请求
            pushplus_url = "https://www.pushplus.plus/send"
            data = {
                'token': self.pushplus_token,
                'title': title,
                'content': content,
                'template': 'html'
            }

            response = requests.post(pushplus_url, json=data, timeout=10)
            result = response.json()

            if result.get('code') == 200:
                self.logger.info(f"成功发送新设备通知，共 {len(new_devices)} 个新设备")
            else:
                self.logger.error(f"发送通知失败: {result.get('msg', '未知错误')}")

        except Exception as e:
            self.logger.error(f"发送通知时发生异常: {str(e)}")

    def set_device_name(self, mac_address, new_name):
        """修改设备名称 - 使用与HA集成相同的模式"""
        if not self.router:
            raise Exception("未登录，请先登录")

        try:
            # 由于HA集成中没有直接的设备改名功能，我们需要使用原始API方法
            # 获取当前认证状态并执行修改
            self.router.authorize()

            # 构造修改设备名称的请求（基于您提供的curl命令）
            # 这里我们需要使用原始的HTTP请求方式
            import requests

            # 获取当前session的cookies
            session = requests.Session()
            session.cookies.update(self.router._session.cookies) if hasattr(self.router, '_session') else None
            session.verify = False

            # 构造请求URL和数据
            base_url = self.router.host.rstrip('/')
            stok = getattr(self.router, '_stok', None)

            if not stok:
                # 尝试从session或其他地方获取stok
                raise Exception("无法获取认证token")

            # 将MAC地址格式从 xx:xx:xx:xx:xx:xx 转换为 xx-xx-xx-xx-xx-xx (路由器需要的格式)
            mac_for_router = mac_address.replace(':', '-')

            set_name_url = f"{base_url}/stok={stok}/ds"
            set_name_data = {
                "hosts_info": {
                    "set_name": {
                        "mac": mac_for_router,
                        "name": new_name,
                        "down_limit": "0",
                        "up_limit": "0",
                        "is_blocked": "0"
                    }
                },
                "method": "do"
            }

            response = session.post(
                set_name_url,
                json=set_name_data,
                headers={'Content-Type': 'application/json; charset=UTF-8'},
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result.get('error_code') == 0:
                return True
            else:
                raise Exception(f"修改设备名称失败: {result.get('error_msg', '未知错误')}")

        except Exception as e:
            raise Exception(f"修改设备名称失败: {str(e)}")

    def batch_set_device_names(self, device_updates, progress_callback=None):
        """批量修改设备名称"""
        results = []
        total_count = len(device_updates)

        for i, update in enumerate(device_updates):
            try:
                success = self.set_device_name(update['mac_address'], update['new_name'])
                result = {
                    'mac_address': update['mac_address'],
                    'new_name': update['new_name'],
                    'success': success,
                    'error': None
                }
                results.append(result)

                # 调用进度回调
                if progress_callback:
                    progress_callback(i + 1, total_count, result)

                time.sleep(0.5)  # 避免请求过快

            except Exception as e:
                result = {
                    'mac_address': update['mac_address'],
                    'new_name': update['new_name'],
                    'success': False,
                    'error': str(e)
                }
                results.append(result)

                # 调用进度回调
                if progress_callback:
                    progress_callback(i + 1, total_count, result)

        return results

# 全局管理器实例
tplink_manager = TPLinkManager()

# 全局进度存储
import threading
progress_data = {
    'current': 0,
    'total': 0,
    'results': [],
    'completed': False,
    'error': None,
    'lock': threading.Lock()
}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    """登录路由器"""
    try:
        data = request.json
        host = data.get('host')
        password = data.get('password')

        if not host or not password:
            return jsonify({'error': '请提供主机地址和密码'}), 400

        success = tplink_manager.login(host, password)

        if success:
            return jsonify({'message': '登录成功'})
        else:
            return jsonify({'error': '登录失败'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """获取设备列表"""
    try:
        # 获取筛选参数
        filter_type = request.args.get('filter', 'all')  # all, unnamed, custom
        sort_by = request.args.get('sort', 'name')       # name, mac, ip, type

        devices = tplink_manager.get_devices()

        # 检查新设备并发送通知
        try:
            tplink_manager.check_and_notify_new_devices(devices)
        except Exception as e:
            # 通知失败不影响设备列表获取
            logger.error(f"检查新设备时发生错误: {str(e)}")

        # 筛选设备
        if filter_type == 'unnamed':
            # 筛选未自定义命名的设备（设备名称与MAC地址相同）
            devices = [d for d in devices if d['name'] == d['mac_address']]
        elif filter_type == 'custom':
            # 筛选已自定义命名的设备
            devices = [d for d in devices if d['name'] != d['mac_address']]

        # 排序设备
        if sort_by == 'name':
            devices.sort(key=lambda x: x['name'])
        elif sort_by == 'mac':
            devices.sort(key=lambda x: x['mac_address'])
        elif sort_by == 'ip':
            devices.sort(key=lambda x: x['ip_address'])
        elif sort_by == 'type':
            devices.sort(key=lambda x: x['connection_type'])

        return jsonify({'devices': devices})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/device/<mac_address>/name', methods=['PUT'])
def set_device_name(mac_address):
    """修改设备名称"""
    try:
        data = request.json
        new_name = data.get('name')

        if not new_name:
            return jsonify({'error': '请提供新名称'}), 400

        success = tplink_manager.set_device_name(mac_address, new_name)

        if success:
            return jsonify({'message': '修改成功'})
        else:
            return jsonify({'error': '修改失败'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/devices/batch-name', methods=['POST'])
def batch_set_device_names():
    """批量修改设备名称"""
    try:
        data = request.json
        device_updates = data.get('devices', [])

        if not device_updates:
            return jsonify({'error': '请提供要更新的设备列表'}), 400

        results = tplink_manager.batch_set_device_names(device_updates)
        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/devices/export')
def export_devices():
    """导出设备列表为CSV"""
    try:
        devices = tplink_manager.get_devices()

        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        writer.writerow(['MAC地址', '设备名称', 'IP地址', '连接类型', '新名称'])

        # 写入设备信息
        for device in devices:
            writer.writerow([
                device['mac_address'],
                device['name'],
                device['ip_address'],
                device['connection_type'],
                ''  # 新名称列为空
            ])

        output.seek(0)

        # 创建响应
        response = send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # 添加BOM以支持中文
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'tplink_devices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/progress', methods=['GET'])
def get_progress():
    """获取批量操作进度"""
    with progress_data['lock']:
        return jsonify({
            'current': progress_data['current'],
            'total': progress_data['total'],
            'percentage': round((progress_data['current'] / progress_data['total'] * 100), 1) if progress_data['total'] > 0 else 0,
            'completed': progress_data['completed'],
            'error': progress_data['error'],
            'latest_result': progress_data['results'][-1] if progress_data['results'] else None
        })

@app.route('/api/devices/import', methods=['POST'])
def import_devices():
    """导入CSV批量更新设备名称"""
    try:
        # 重置进度数据
        with progress_data['lock']:
            progress_data['current'] = 0
            progress_data['total'] = 0
            progress_data['results'] = []
            progress_data['completed'] = False
            progress_data['error'] = None

        if 'file' not in request.files:
            return jsonify({'error': '请上传CSV文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '请选择文件'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'error': '请上传CSV格式文件'}), 400

        # 读取CSV文件
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))  # 处理BOM
        csv_reader = csv.DictReader(stream)

        # 获取当前设备列表，用于对比
        current_devices = {}
        try:
            devices = tplink_manager.get_devices()
            for device in devices:
                current_devices[device['mac_address']] = device['name']
        except:
            pass  # 如果获取设备列表失败，继续处理

        device_updates = []
        skipped_count = 0
        unchanged_count = 0

        # 读取所有行进行统计
        all_rows = list(csv_reader)
        for row in all_rows:
            mac_address = row.get('MAC地址') or row.get('mac_address') or row.get('mac')
            new_name = row.get('新名称') or row.get('new_name')
            current_name = row.get('设备名称') or row.get('device_name') or row.get('name')

            if mac_address:
                # 确保MAC地址格式为 xx:xx:xx:xx:xx:xx
                mac_clean = mac_address.strip().upper().replace('-', ':')

                # 处理新名称字段
                if new_name and new_name.strip():
                    # 有新名称，需要更新
                    device_updates.append({
                        'mac_address': mac_clean,
                        'new_name': new_name.strip()
                    })
                elif current_name and current_name.strip():
                    # 检查当前名称是否与实际的设备名称不同
                    if mac_clean in current_devices and current_devices[mac_clean] != current_name.strip():
                        # CSV中的当前名称与路由器中的不同，说明设备名称已经被修改过
                        device_updates.append({
                            'mac_address': mac_clean,
                            'new_name': current_name.strip()
                        })
                    else:
                        unchanged_count += 1
                else:
                    # 新名称为空，跳过此设备
                    skipped_count += 1

        total_rows = len(all_rows)

        if not device_updates:
            return jsonify({
                'error': 'CSV文件中没有需要更新的设备',
                'details': f'跳过 {skipped_count} 个空名称设备，保持 {unchanged_count} 个设备名称不变'
            }), 400

        # 设置进度总数
        with progress_data['lock']:
            progress_data['total'] = len(device_updates)

        # 定义进度回调函数
        def progress_callback(current, total, result):
            with progress_data['lock']:
                progress_data['current'] = current
                progress_data['results'].append(result)

        # 在后台线程中执行批量更新
        def batch_update_thread():
            try:
                results = tplink_manager.batch_set_device_names(device_updates, progress_callback)
                success_count = sum(1 for r in results if r['success'])

                with progress_data['lock']:
                    progress_data['completed'] = True

                # 这里不返回结果，等待前端查询获取

            except Exception as e:
                with progress_data['lock']:
                    progress_data['error'] = str(e)
                    progress_data['completed'] = True

        # 启动后台线程
        thread = threading.Thread(target=batch_update_thread)
        thread.daemon = True
        thread.start()

        # 立即返回响应，让前端开始轮询进度
        return jsonify({
            'message': f'开始批量更新 {len(device_updates)} 个设备...',
            'summary': {
                'total_devices': total_rows,
                'updates_attempted': len(device_updates),
                'skipped_count': skipped_count,
                'unchanged_count': unchanged_count
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)