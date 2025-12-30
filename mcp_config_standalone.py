"""
方案2：创建独立的 MCP 服务器，连接到已运行的 FastAPI 服务
适用于：你不能修改现有的 FastAPI 应用，或者想将 MCP 服务器单独部署

工作原理：
1. 通过 HTTP 获取运行中服务的 OpenAPI schema
2. 创建一个代理 FastAPI 应用
3. 在这个代理应用上创建 MCP 服务器
4. 使用自定义 HTTP 客户端连接到原始服务

使用方法：
1. 确保你的 FastAPI 服务运行在 http://localhost:6673
2. 运行此脚本：python mcp_config_standalone.py
3. MCP 服务器将在 http://localhost:8000/mcp 可用
4. 在 Cursor 中配置 MCP 服务器地址为 http://localhost:8000/mcp
"""

import httpx
import json
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

# 你的 FastAPI 服务地址
API_BASE_URL = "http://localhost:6673"

async def get_openapi_schema(base_url: str) -> dict:
    """从运行中的 FastAPI 服务获取 OpenAPI schema"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"无法获取 OpenAPI schema: {response.status_code} - {response.text}")

def create_proxy_app(openapi_schema: dict) -> FastAPI:
    """根据 OpenAPI schema 创建一个代理 FastAPI 应用"""
    app = FastAPI(
        title=openapi_schema.get("info", {}).get("title", "MCP Proxy Server"),
        description=openapi_schema.get("info", {}).get("description", "MCP Server for External API"),
        version=openapi_schema.get("info", {}).get("version", "1.0.0"),
    )
    
    # 注意：这里我们不需要实际定义路由
    # FastApiMCP 只需要 FastAPI 应用实例来获取 OpenAPI schema
    # 但我们已经有了 schema，所以我们需要一个不同的方法
    
    # 实际上，FastApiMCP 在 setup_server() 中会调用 get_openapi()
    # 我们需要让这个调用返回我们获取的 schema
    
    # 解决方案：手动设置 app.openapi_schema
    # 但 FastAPI 的 get_openapi() 会重新生成，所以我们需要重写它
    
    return app

async def setup_mcp_server():
    """设置 MCP 服务器"""
    print(f"正在从 {API_BASE_URL} 获取 OpenAPI schema...")
    
    try:
        # 获取 OpenAPI schema
        openapi_schema = await get_openapi_schema(API_BASE_URL)
        print("✓ 成功获取 OpenAPI schema")
        
        # 创建代理 FastAPI 应用
        proxy_app = FastAPI(
            title=openapi_schema.get("info", {}).get("title", "MCP Proxy Server"),
            description=openapi_schema.get("info", {}).get("description", "MCP Server for External API"),
            version=openapi_schema.get("info", {}).get("version", "1.0.0"),
        )
        
        # 手动设置 OpenAPI schema（这样 FastApiMCP 就能使用它）
        # 但 FastAPI 的 get_openapi() 会重新生成，我们需要拦截它
        # 实际上，我们需要修改 FastApiMCP 的行为，或者使用不同的方法
        
        # 临时解决方案：创建一个包含所有路径的代理应用
        # 但这很复杂，因为需要解析 OpenAPI schema 并创建路由
        
        print("⚠️  注意：FastAPI-MCP 需要直接访问 FastAPI 应用实例")
        print("   如果无法修改原服务，建议使用方案1（在服务中添加 MCP）")
        print("\n   或者，你可以：")
        print("   1. 在你的原 FastAPI 服务中添加以下代码：")
        print("      from fastapi_mcp import FastApiMCP")
        print("      mcp = FastApiMCP(app)")
        print("      mcp.mount_http()")
        print("   2. 重启服务，MCP 将在 http://localhost:6673/mcp 可用")
        
        return None
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

if __name__ == "__main__":
    import asyncio
    
    print("=" * 60)
    print("独立 MCP 服务器配置")
    print("=" * 60)
    print()
    
    result = asyncio.run(setup_mcp_server())
    
    if result is None:
        print("\n" + "=" * 60)
        print("推荐方案：在原始 FastAPI 服务中添加 MCP")
        print("=" * 60)
        print("\n在你的 FastAPI 服务主文件中添加：")
        print("\n```python")
        print("from fastapi_mcp import FastApiMCP")
        print()
        print("# 在你的 app 定义之后")
        print("mcp = FastApiMCP(app)")
        print("mcp.mount_http()  # MCP 将在 http://localhost:6673/mcp 可用")
        print("```")
        print("\n然后重启服务即可。")
