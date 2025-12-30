# FastAPI MCP 配置说明

为运行在 `http://localhost:6673` 的 FastAPI 服务创建独立的 MCP 服务器，并在 Cursor 中配置。

## 架构说明

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│  FastAPI 服务   │         │   MCP 服务器      │         │   Cursor    │
│  localhost:6673 │ ◄────── │  localhost:8000   │ ◄────── │   AI 客户端 │
│  (接口服务)     │         │  /mcp             │         │             │
└─────────────────┘         └──────────────────┘         └─────────────┘
```

- **FastAPI 服务**：你的原始 API 服务，运行在 6673 端口
- **MCP 服务器**：独立的 MCP 服务器，运行在 8000 端口，连接到 FastAPI 服务
- **Cursor**：AI 客户端，通过 MCP 协议连接到 MCP 服务器

---

## 快速开始

### 步骤 1：确保 FastAPI 服务正在运行

确保你的 FastAPI 服务运行在 `http://localhost:6673`，并且可以访问：
- `http://localhost:6673/docs` - Swagger 文档
- `http://localhost:6673/openapi.json` - OpenAPI schema（MCP 服务器需要这个）

### 步骤 2：启动 MCP 服务器

运行以下命令：

```bash
python run_mcp_server.py
```

你会看到类似以下的输出：

```
======================================================================
MCP 服务器设置
======================================================================

FastAPI 服务地址: http://localhost:6673
MCP 服务器地址: http://0.0.0.0:8000/mcp

正在从 FastAPI 服务获取 OpenAPI schema...
✓ 成功获取 OpenAPI schema
  - 服务名称: 你的 API 名称
  - 版本: 1.0.0
  - 路径数量: 10

正在创建 MCP 代理应用...
正在创建代理路由...
✓ 已创建 10 个代理路由

正在创建 MCP 服务器...
✓ MCP 服务器创建完成

======================================================================
🎉 MCP 服务器已启动！
======================================================================

MCP 服务器地址: http://localhost:8000/mcp
FastAPI 服务地址: http://localhost:6673
```

### 步骤 3：在 Cursor 中配置 MCP 服务器

1. **打开 Cursor 设置**
   - Windows/Linux: `Ctrl + ,` 或 `File > Preferences > Settings`
   - Mac: `Cmd + ,` 或 `Cursor > Preferences > Settings`

2. **找到 MCP 配置**
   - 在设置中搜索 "MCP" 或 "Model Context Protocol"
   - 或者直接编辑配置文件：
     - Windows: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
     - Mac: `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
     - Linux: `~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

3. **添加 MCP 服务器配置**

   添加以下配置：

   ```json
   {
     "mcpServers": {
       "my-fastapi-service": {
         "url": "http://localhost:8000/mcp"
       }
     }
   }
   ```

   如果已经有其他 MCP 服务器，添加新的条目：

   ```json
   {
     "mcpServers": {
       "existing-server": {
         "url": "http://existing-server/mcp"
       },
       "my-fastapi-service": {
         "url": "http://localhost:8000/mcp"
       }
     }
   }
   ```

4. **保存配置并重启 Cursor**

5. **验证配置**

   在 Cursor 中问 AI：
   - "列出所有可用的工具"
   - "有哪些 MCP 工具可以使用？"

   AI 应该能够列出你的 FastAPI 接口作为可用工具。

---

## 测试 MCP 服务器

### 测试 1：检查 MCP 服务器是否运行

在浏览器中访问：
```
http://localhost:8000/mcp
```

应该能看到 MCP 服务器的响应（可能是 JSON 或 HTML）。

### 测试 2：在 Cursor 中测试

在 Cursor 中问 AI：

```
请列出所有可用的工具，并告诉我每个工具的用途
```

AI 应该能够列出你的 FastAPI 接口。

### 测试 3：实际调用接口

根据你的 API 接口，问 AI 相应的问题，例如：

- 如果你的 API 有用户接口：`"获取用户 ID 为 1 的信息"`
- 如果你的 API 有商品接口：`"列出所有商品"`
- 等等...

---

## 配置选项

### 修改 MCP 服务器端口

编辑 `run_mcp_server.py`，修改以下变量：

```python
MCP_SERVER_PORT = 8000  # 改为你想要的端口
```

### 修改 FastAPI 服务地址

如果 FastAPI 服务不在 localhost:6673，编辑 `run_mcp_server.py`：

```python
FASTAPI_SERVICE_URL = "http://your-api-host:6673"
```

### 修改 MCP 挂载路径

```python
MCP_MOUNT_PATH = "/mcp"  # 改为你想要的路径
```

然后在 Cursor 配置中使用新的路径：
```json
{
  "mcpServers": {
    "my-fastapi-service": {
      "url": "http://localhost:8000/your-custom-path"
    }
  }
}
```

---

## 故障排除

### 问题 1：无法连接到 FastAPI 服务

**错误信息：**
```
无法连接到 FastAPI 服务 http://localhost:6673
```

**解决方案：**
1. 确保 FastAPI 服务正在运行
2. 检查服务是否在 6673 端口
3. 测试访问 `http://localhost:6673/docs` 是否正常
4. 检查防火墙设置

### 问题 2：无法获取 OpenAPI schema

**错误信息：**
```
获取 OpenAPI schema 失败: 404
```

**解决方案：**
1. 确保 FastAPI 服务可以访问 `/openapi.json`
2. 在浏览器中测试：`http://localhost:6673/openapi.json`
3. 检查 FastAPI 应用是否正确配置了 OpenAPI

### 问题 3：Cursor 无法连接到 MCP 服务器

**解决方案：**
1. 确保 MCP 服务器正在运行（检查终端输出）
2. 检查 Cursor 配置中的 URL 是否正确
3. 确保端口没有被其他程序占用
4. 尝试重启 Cursor
5. 检查 Cursor 的 MCP 日志（如果有）

### 问题 4：AI 无法识别工具

**解决方案：**
1. 确保 FastAPI 接口有 `operation_id`
2. 确保接口有清晰的 `summary` 和 `description`
3. 检查 MCP 服务器日志，看是否有错误
4. 在 Cursor 中重新加载 MCP 配置

### 问题 5：调用接口失败

**解决方案：**
1. 检查接口是否需要认证
2. 查看 MCP 服务器和 FastAPI 服务的日志
3. 检查接口参数是否正确
4. 测试直接调用 FastAPI 接口是否正常

---

## 高级配置

### 自定义超时时间

编辑 `run_mcp_server.py`，在 `setup_mcp_server()` 函数中：

```python
http_client = httpx.AsyncClient(
    base_url=FASTAPI_SERVICE_URL,
    timeout=60.0,  # 增加超时时间（秒）
)
```

### 添加认证

如果你的 FastAPI 服务需要认证，MCP 服务器会自动转发 `authorization` 头。

在 Cursor 中调用工具时，如果需要认证，可以在 MCP 配置中添加：

```json
{
  "mcpServers": {
    "my-fastapi-service": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-token-here"
      }
    }
  }
}
```

---

## 工作原理

1. **MCP 服务器启动时**：
   - 从 FastAPI 服务获取 OpenAPI schema
   - 根据 schema 创建代理路由
   - 将 FastAPI 接口转换为 MCP 工具

2. **AI 调用工具时**：
   - Cursor 通过 MCP 协议发送工具调用请求
   - MCP 服务器接收请求
   - MCP 服务器将请求转发到 FastAPI 服务
   - 返回结果给 Cursor/AI

3. **工具发现**：
   - AI 通过 `list_tools()` 获取所有可用工具
   - 每个工具包含名称、描述、参数等信息
   - AI 根据用户问题和工具描述决定调用哪个工具

---

## 更多信息

- 查看 `run_mcp_server.py` 了解详细实现
- 查看项目文档：https://github.com/tadata-org/fastapi_mcp
- 查看示例：`examples/` 目录

---

## 快速参考

```bash
# 启动 MCP 服务器
python run_mcp_server.py

# Cursor MCP 配置
{
  "mcpServers": {
    "my-fastapi-service": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```
