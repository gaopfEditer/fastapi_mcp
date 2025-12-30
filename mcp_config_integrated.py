"""
方案1：在现有的 FastAPI 服务中直接集成 MCP 服务器
适用于：你可以修改现有的 FastAPI 应用代码

使用方法：
1. 在你的 FastAPI 应用主文件中导入并添加以下代码
2. 重启服务，MCP 服务器将在 http://localhost:6673/mcp 可用
"""

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import httpx

# 假设这是你现有的 FastAPI 应用
# 如果你已经有 app 实例，直接使用它
# app = FastAPI()  # 或者你现有的 app 实例

# 创建 MCP 服务器
# 如果你的 FastAPI 应用已经定义好了，直接传入
# mcp = FastApiMCP(app)

# 如果需要在创建 app 之后添加，可以这样做：
# mcp = FastApiMCP(app, name="我的 API MCP 服务")
# mcp.mount_http()  # 挂载到 /mcp 路径

# 完整示例：
"""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

# 你的现有 FastAPI 应用
app = FastAPI(title="我的 API 服务")

# 你的现有路由...
@app.get("/")
async def root():
    return {"message": "Hello World"}

# 添加 MCP 服务器
mcp = FastApiMCP(app, name="我的 API MCP 服务")
mcp.mount_http()  # MCP 服务器将在 http://localhost:6673/mcp 可用

# 运行服务（如果这是主文件）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6673)
"""

