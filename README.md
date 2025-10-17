# TP-Link Device Manager

A web-based TP-Link router device management tool with batch device renaming capabilities, CSV import/export functionality, and Docker deployment support.

## Features

- 🔐 **Router Authentication** - Support for TP-Link router web login
- 📱 **Device List Display** - Real-time display of all connected device information
- ✏️ **Individual Device Renaming** - Direct device name editing in the interface
- 📊 **Auto-refresh** - Optional 10-second auto-refresh for device list
- 📥 **CSV Export** - Export current device list for editing
- 📤 **CSV Import** - Batch import of modified device names
- 🐳 **Docker Support** - Complete Docker deployment solution
- 📢 **WeChat Notifications** - New device connection alerts via PushPlus

## Quick Start

### Docker Deployment (Recommended)

#### Option 1: Using Docker Compose (Recommended)
```bash
docker-compose up -d
```
Access `http://localhost:8080`

#### Option 2: Using Docker directly
```bash
docker run -d -p 8080:8080 --name tplink-device-manager lisankai93/tplink-device-manager:latest
```
Access `http://localhost:8080`

### Local Development

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access `http://localhost:8080`

## Usage

### 1. Router Login
- Enter your router's internal IP address (e.g., 192.168.1.1)
- Enter the login password
- Click the "Login" button

### 2. View Device List
- After successful login, all connected devices are automatically displayed
- Includes device name, MAC address, IP address, connection type, and more

### 3. Rename Devices
- **Individual renaming**: Edit device name directly in the device list, click "Rename" button
- **Batch renaming**:
  1. Click "Export CSV" to download current device list
  2. Edit the "New Name" column in Excel or other tools
  3. Click "Import CSV" to upload the modified file
  4. System automatically processes in batch and displays results

### 4. Auto-refresh
- Enable "Auto-refresh" toggle to automatically update device list every 10 seconds
- Disable to stop automatic refresh

## CSV File Format

The exported CSV file contains the following columns:
- MAC Address: Device MAC address (unique identifier)
- Device Name: Current device name
- IP Address: Current IP address of the device
- Connection Type: Device connection type
- New Name: **Please fill in the new name to change here**

## Docker Compose Configuration

```yaml
version: '3.8'
services:
  tplink-device-manager:
    image: lisankai93/tplink-device-manager:latest
    container_name: tplink-device-manager
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - FLASK_PORT=8080
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Environment Variables

- `FLASK_ENV`: Flask environment mode (development/production)
- `FLASK_PORT`: Port to run on (default: 8080)
- `PUSHPLUS_TOKEN`: PushPlus notification token for WeChat alerts (optional)
- `AUTO_MONITOR`: Enable automatic device monitoring (true/false, default: false)
- `MONITOR_INTERVAL`: Monitoring interval in seconds (default: 300, minimum: 60)

## Automatic Device Monitoring

The application supports automatic device monitoring for seamless new device detection without manual intervention.

### Features

- 🔒 **Auto Login**: Remembers router credentials after first login
- 🔄 **Periodic Checks**: Automatically checks for new devices at specified intervals
- 📢 **Instant Notifications**: Sends WeChat notifications when new devices are detected
- 🛡️ **Secure**: Credentials are stored locally in the container

### Setup Instructions

1. **Enable Automatic Monitoring**
   ```yaml
   environment:
     - AUTO_MONITOR=true  # 启用自动监控
     - MONITOR_INTERVAL=300  # 5分钟检查一次
   ```

2. **First Login with Monitoring**
   ```json
   {
     "host": "192.168.1.1",
     "password": "your_router_password",
     "enable_auto_monitor": true
   }
   ```

3. **Monitor Status**
   - Check monitoring status: `GET /api/monitor/status`
   - Manual trigger: `POST /api/monitor/trigger`
   - Update settings: `PUT /api/monitor`

### Behavior

- When enabled, the system saves your router credentials securely
- Automatically checks for new devices every 5 minutes (configurable)
- Only sends notifications for truly new devices or unnamed devices
- Failed monitoring attempts don't affect the web interface
- Credentials persist across container restarts

### Configuration Options

- `AUTO_MONITOR=false`: Disable automatic monitoring (default)
- `AUTO_MONITOR=true`: Enable automatic monitoring
- `MONITOR_INTERVAL=300`: Check every 300 seconds (5 minutes minimum)

## WeChat Notifications

The application supports sending WeChat notifications when new devices connect to your network using PushPlus.

### Setup Instructions

1. **Get PushPlus Token**
   - Visit [PushPlus](https://www.pushplus.plus/)
   - Register and get your token

2. **Configure Docker Compose**
   ```yaml
   environment:
     - PUSHPLUS_TOKEN=your_actual_token_here
   ```

3. **Notification Content**
   - **Title**: "有新的设备连接到家庭网络了"
   - **Content**: Device name, IP address, and MAC address in HTML format
   - **Template**: HTML formatted for better readability

4. **Behavior**
   - Notifications are only sent when devices connect for the first time
   - Each device is tracked by its MAC address
   - If no token is configured, no notifications will be sent
   - Failed notifications don't affect device list functionality

### Example Notification

```
Title: 有新的设备连接到家庭网络了

Content:
检测到新设备连接
请注意：以下设备是首次连接到家庭网络，请及时固定IP地址并修改设备名称。

设备名称: iPhone-123
IP地址: 192.168.1.100
MAC地址: AA:BB:CC:DD:EE:FF
```

## API Endpoints

### Authentication
- `POST /api/login` - Login to router

### Automatic Monitoring
- `GET /api/monitor/status` - Get monitoring status
- `POST /api/monitor/trigger` - Manually trigger monitoring
- `PUT /api/monitor` - Update monitoring settings

### Device Management
- `GET /api/devices` - Get device list (includes monitoring status)
- `PUT /api/device/<mac_address>/name` - Rename single device
- `POST /api/devices/batch-name` - Batch rename devices

### File Operations
- `GET /api/devices/export` - Export device list as CSV
- `POST /api/devices/import` - Import CSV for batch updates
- `GET /api/progress` - Get batch operation progress

## Troubleshooting

1. **Login Failed**
   - Check if router IP address is correct
   - Confirm password is the router's web login password (not TP-Link ID password)
   - Check network connectivity

2. **Cannot Get Device List**
   - Confirm router model compatibility
   - Check if blocked by router security policies
   - Try re-login

3. **Batch Operation Failed**
   - Check if CSV file format is correct
   - Confirm MAC address format (XX:XX:XX:XX:XX:XX)
   - Check if new names contain special characters

## Security Notes

- Passwords are temporarily stored in memory only, not saved to disk
- Recommended for use in trusted internal network environments
- Regularly update router passwords for security

## Technology Stack

- **Backend**: Python Flask + requests
- **Frontend**: HTML/CSS/JavaScript
- **Deployment**: Docker + Docker Compose
- **API**: RESTful API design

## Docker Images

The project is automatically built and pushed to:
- **GitHub Container Registry**: `ghcr.io/lisankai93/tplink-device-manager`
- **Docker Hub**: `lisankai93/tplink-device-manager`

## Development

### Building Docker Image
```bash
docker build -t tplink-device-manager .
```

### Testing
```bash
# Run the container in development mode
docker run -p 8080:8080 --rm -v $(pwd):/app -w /app tplink-device-manager
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request