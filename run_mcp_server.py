"""
为运行在 localhost:6673 的 FastAPI 服务创建独立的 MCP 服务器

使用方法：
1. 确保你的 FastAPI 服务运行在 http://localhost:6673
2. 运行此脚本：python run_mcp_server.py
3. MCP 服务器将在 http://localhost:8000/mcp 启动
4. 在 Cursor 的 MCP 配置中添加：http://localhost:8000/mcp
"""

import httpx
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from typing import Dict, Any

# ============================================
# 配置
# ============================================
# 你的 FastAPI 服务地址
FASTAPI_SERVICE_URL = "http://localhost:6673"

# MCP 服务器配置
MCP_SERVER_HOST = "0.0.0.0"
MCP_SERVER_PORT = 8000
MCP_MOUNT_PATH = "/mcp"

# ============================================
# 辅助函数
# ============================================

async def fetch_openapi_schema(api_url: str) -> Dict[str, Any]:
    """从 FastAPI 服务获取 OpenAPI schema"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{api_url}/openapi.json")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"无法连接到 FastAPI 服务 {api_url}: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"获取 OpenAPI schema 失败: {e.response.status_code}")

def create_proxy_routes(app: FastAPI, openapi_schema: Dict[str, Any], target_url: str):
    """根据 OpenAPI schema 创建代理路由，将请求转发到目标 FastAPI 服务"""
    paths = openapi_schema.get("paths", {})
    
    def create_proxy_handler(method: str, path_template: str):
        """创建代理处理函数"""
        async def handler(request: Request):
            # 获取请求体
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.json()
                except:
                    try:
                        body = await request.body()
                    except:
                        pass
            
            # 获取查询参数
            query_params = dict(request.query_params)
            
            # 获取请求头（转发授权等）
            headers = {}
            for header_name in ["authorization", "content-type"]:
                if header_name in request.headers:
                    headers[header_name] = request.headers[header_name]
            
            # 构建目标 URL，替换路径参数
            target_path = path_template
            path_params = request.path_params
            for param_name, param_value in path_params.items():
                target_path = target_path.replace(f"{{{param_name}}}", str(param_value))
            
            full_target_url = f"{target_url}{target_path}"
            
            # 发送请求到原始服务
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.request(
                        method=method,
                        url=full_target_url,
                        params=query_params,
                        headers=headers,
                        json=body if body and isinstance(body, dict) else None,
                        content=body if body and not isinstance(body, dict) else None,
                    )
                    
                    # 处理响应
                    if response.headers.get("content-type", "").startswith("application/json"):
                        try:
                            content = response.json()
                        except:
                            content = {"content": response.text}
                    else:
                        content = {"content": response.text}
                    
                    return JSONResponse(
                        content=content,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                    )
                except httpx.RequestError as e:
                    raise HTTPException(status_code=502, detail=f"无法连接到 FastAPI 服务: {e}")
        
        return handler
    
    # 为每个路径和方法创建路由
    route_count = 0
    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch"]:
            if method in path_item:
                operation = path_item[method]
                operation_id = operation.get("operationId")
                if not operation_id:
                    # 如果没有 operation_id，生成一个
                    operation_id = f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '').strip('_')}"
                
                # 创建处理函数
                handler = create_proxy_handler(method.upper(), path)
                
                # 注册路由
                if method == "get":
                    app.get(path, operation_id=operation_id, include_in_schema=True)(handler)
                elif method == "post":
                    app.post(path, operation_id=operation_id, include_in_schema=True)(handler)
                elif method == "put":
                    app.put(path, operation_id=operation_id, include_in_schema=True)(handler)
                elif method == "delete":
                    app.delete(path, operation_id=operation_id, include_in_schema=True)(handler)
                elif method == "patch":
                    app.patch(path, operation_id=operation_id, include_in_schema=True)(handler)
                
                route_count += 1
    
    return route_count

async def setup_mcp_server():
    """设置 MCP 服务器"""
    print("=" * 70)
    print("MCP 服务器设置")
    print("=" * 70)
    print(f"\nFastAPI 服务地址: {FASTAPI_SERVICE_URL}")
    print(f"MCP 服务器地址: http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}{MCP_MOUNT_PATH}")
    print()
    
    # 获取 OpenAPI schema
    print("正在从 FastAPI 服务获取 OpenAPI schema...")
    try:
        openapi_schema = await fetch_openapi_schema(FASTAPI_SERVICE_URL)
        print(f"✓ 成功获取 OpenAPI schema")
        print(f"  - 服务名称: {openapi_schema.get('info', {}).get('title', 'Unknown')}")
        print(f"  - 版本: {openapi_schema.get('info', {}).get('version', 'Unknown')}")
        print(f"  - 路径数量: {len(openapi_schema.get('paths', {}))}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n请确保：")
        print(f"  1. FastAPI 服务运行在 {FASTAPI_SERVICE_URL}")
        print(f"  2. 服务可以访问 /openapi.json 端点")
        return None
    
    # 创建代理 FastAPI 应用
    print("\n正在创建 MCP 代理应用...")
    proxy_app = FastAPI(
        title=f"MCP Server for {openapi_schema.get('info', {}).get('title', 'API')}",
        description=f"MCP 服务器，连接到 {FASTAPI_SERVICE_URL}",
        version="1.0.0",
    )
    
    # 创建代理路由
    print("正在创建代理路由...")
    route_count = create_proxy_routes(proxy_app, openapi_schema, FASTAPI_SERVICE_URL)
    print(f"✓ 已创建 {route_count} 个代理路由")
    
    # 创建 MCP 服务器
    print("\n正在创建 MCP 服务器...")
    try:
        # 使用自定义 HTTP 客户端连接到原始 FastAPI 服务
        http_client = httpx.AsyncClient(
            base_url=FASTAPI_SERVICE_URL,
            timeout=30.0,
        )
        
        mcp = FastApiMCP(
            proxy_app,
            name=f"MCP Server for {openapi_schema.get('info', {}).get('title', 'API')}",
            http_client=http_client,
        )
        
        mcp.mount_http(mount_path=MCP_MOUNT_PATH)
        print("✓ MCP 服务器创建完成")
        
        print("\n" + "=" * 70)
        print("🎉 MCP 服务器已启动！")
        print("=" * 70)
        print(f"\nMCP 服务器地址: http://localhost:{MCP_SERVER_PORT}{MCP_MOUNT_PATH}")
        print(f"FastAPI 服务地址: {FASTAPI_SERVICE_URL}")
        print("\n" + "-" * 70)
        print("在 Cursor 中配置 MCP 服务器：")
        print("-" * 70)
        print("\n1. 打开 Cursor 设置")
        print("2. 找到 MCP 配置")
        print("3. 添加以下配置：")
        print()
        print(json.dumps({
            "mcpServers": {
                "my-fastapi-service": {
                    "url": f"http://localhost:{MCP_SERVER_PORT}{MCP_MOUNT_PATH}"
                }
            }
        }, indent=2, ensure_ascii=False))
        print()
        print("4. 重启 Cursor")
        print("5. 在 Cursor 中问 AI：'列出所有可用的工具' 来验证")
        print("\n" + "=" * 70)
        
        return proxy_app
        
    except Exception as e:
        print(f"❌ 创建 MCP 服务器失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    proxy_app = asyncio.run(setup_mcp_server())
    
    if proxy_app:
        print(f"\n启动 MCP 服务器在端口 {MCP_SERVER_PORT}...")
        print("按 Ctrl+C 停止服务器\n")
        
        import uvicorn
        uvicorn.run(proxy_app, host=MCP_SERVER_HOST, port=MCP_SERVER_PORT, log_level="info")
    else:
        print("\n❌ 无法启动 MCP 服务器")

if __name__ == "__main__":
    main()

