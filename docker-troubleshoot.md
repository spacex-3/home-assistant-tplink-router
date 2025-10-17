# Docker 部署故障排除指南

## 错误：manifest for lisankai93/tplink-device-manager:latest not found

### 问题原因
Docker Hub 镜像可能还没有完全同步，或者没有 `latest` 标签。

### 解决方案

#### 方案 1：等待同步（推荐）
Docker Hub 镜像推送后需要几分钟时间才能完全同步到全球 CDN。建议：
```bash
# 等待 2-5 分钟后重试
docker compose up -d
```

#### 方案 2：检查可用标签
```bash
# 检查 Docker Hub 上的可用标签
# 访问: https://hub.docker.com/r/lisankai93/tplink-device-manager/tags

# 如果发现具体标签，替换 docker-compose.yml 中的 latest
# 例如：
image: lisankai93/tplink-device-manager:v1.0.0
```

#### 方案 3：手动拉取验证
```bash
# 验证镜像是否存在
docker pull lisankai93/tplink-device-manager:latest

# 如果失败，尝试拉取具体版本
docker pull lisankai93/tplink-device-manager:v1.0.0
```

#### 方案 4：使用镜像摘要（如果标签不确定）
```yaml
# 在 docker-compose.yml 中使用镜像摘要
services:
  tplink-device-manager:
    image: lisankai93/tplink-device-manager@sha256:abc123...  # 替换为实际的镜像摘要
```

### 验证镜像部署成功
```bash
# 查看容器状态
docker ps | grep tplink-device-manager

# 查看容器日志
docker logs tplink-device-manager

# 测试应用访问
curl http://localhost:8080/
```

### Docker Compose 配置示例
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
    # 如果镜像拉取失败，使用以下策略
    pull_policy: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 常见问题

1. **镜像不存在**: 检查 Docker Hub 控制台，确认镜像已成功推送
2. **网络问题**: 使用加速器或检查网络连接
3. **缓存问题**: 清理 Docker 缓存: `docker system prune`
4. **权限问题**: 确认 Docker Hub 凭据正确

### 检查镜像状态
访问以下链接确认镜像状态：
- [Docker Hub - lisankai93/tplink-device-manager](https://hub.docker.com/r/lisankai93/tplink-device-manager)
- 点击 "Tags" 查看所有可用标签