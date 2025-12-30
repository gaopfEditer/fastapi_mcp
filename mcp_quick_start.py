"""
快速开始：为运行在 localhost:6673 的 FastAPI 服务添加 MCP 支持

使用方法：
1. 在你的 FastAPI 服务主文件中添加以下代码
2. 重启服务
3. MCP 服务器将在 http://localhost:6673/mcp 可用
4. 在 Cursor 中配置 MCP 服务器地址为 http://localhost:6673/mcp
"""

# ============================================
# 在你的 FastAPI 服务主文件中添加以下代码
# ============================================

from fastapi_mcp import FastApiMCP

# 假设你的 FastAPI 应用实例名为 app
# 在你的所有路由定义之后，添加：

# 创建 MCP 服务器
# 注意：这里的 app 是你的 FastAPI 应用实例
mcp = FastApiMCP(
    app,  # noqa: F821
    name="我的 API MCP 服务",  # 可选：自定义 MCP 服务器名称
    # describe_full_response_schema=True,  # 可选：包含完整的响应 schema
    # describe_all_responses=True,  # 可选：包含所有响应类型
)

# 挂载 MCP 服务器（使用 HTTP 传输，推荐）
mcp.mount_http()  # MCP 服务器将在 http://localhost:6673/mcp 可用

# 或者使用 SSE 传输（向后兼容）
# mcp.mount_sse()  # MCP 服务器将在 http://localhost:6673/sse 可用

# ============================================
# 完整示例
# ============================================

"""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

# 你的 FastAPI 应用
app = FastAPI(title="我的 API 服务", version="1.0.0")

# 你的路由定义
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/users/{user_id}", operation_id="get_user")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "John"}

# 添加 MCP 服务器（在所有路由定义之后）
mcp = FastApiMCP(app, name="我的 API MCP 服务")
mcp.mount_http()

# 运行服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6673)
"""

# ============================================
# 在 Cursor 中配置 MCP 服务器
# ============================================

"""
1. 打开 Cursor 设置
2. 找到 MCP 配置
3. 添加以下配置：

{
  "mcpServers": {
    "my-api": {
      "url": "http://localhost:6673/mcp"
    }
  }
}

4. 重启 Cursor
5. AI 将能够调用你的 FastAPI 接口
"""

# ============================================
# 高级配置选项
# ============================================

"""
# 1. 自定义超时时间
import httpx
from fastapi_mcp import FastApiMCP

custom_client = httpx.AsyncClient(timeout=30.0)
mcp = FastApiMCP(app, http_client=custom_client)
mcp.mount_http()

# 2. 只暴露特定的接口
mcp = FastApiMCP(
    app,
    include_operations=["get_user", "create_user"]  # 只包含这些操作
)
mcp.mount_http()

# 3. 排除特定的接口
mcp = FastApiMCP(
    app,
    exclude_operations=["delete_user"]  # 排除这个操作
)
mcp.mount_http()

# 4. 按标签过滤
mcp = FastApiMCP(
    app,
    include_tags=["public", "users"]  # 只包含这些标签的接口
)
mcp.mount_http()

# 5. 包含完整的响应 schema
mcp = FastApiMCP(
    app,
    describe_full_response_schema=True,  # 在工具描述中包含完整的 JSON schema
    describe_all_responses=True  # 包含所有响应类型（不仅仅是成功响应）
)
mcp.mount_http()
"""

