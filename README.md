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

## Quick Start

### Docker Deployment (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd tplink-device-manager
```

2. Build and run with Docker:
```bash
# Build the image
docker build -t tplink-device-manager .

# Run the container
docker run -d -p 8080:8080 --name tplink-manager tplink-device-manager
```

Or use Docker Compose:
```bash
docker-compose up -d
```

3. Access `http://localhost:8080`

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
  tplink-manager:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

## Environment Variables

- `FLASK_ENV`: Flask environment mode (development/production)
- `FLASK_DEBUG`: Enable debug mode (true/false)
- `FLASK_PORT`: Port to run on (default: 8080)

## API Endpoints

### Authentication
- `POST /api/login` - Login to router

### Device Management
- `GET /api/devices` - Get device list
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