"""
独立 MCP 代理服务器
从运行在 localhost:6673 的 FastAPI 服务创建独立的 MCP 服务器

使用方法：
1. 确保你的 FastAPI 服务运行在 http://localhost:6673
2. 运行：python mcp_proxy_server.py
3. MCP 服务器将在 http://localhost:8000/mcp 可用
4. 在 Cursor 中配置：http://localhost:8000/mcp

注意：这个方案需要能够访问原服务的 OpenAPI schema
"""

import httpx
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from typing import Dict, Any

# 原始 FastAPI 服务的地址
ORIGINAL_API_URL = "http://localhost:6673"
MCP_SERVER_PORT = 8000

async def fetch_openapi_schema() -> Dict[str, Any]:
    """从原始服务获取 OpenAPI schema"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{ORIGINAL_API_URL}/openapi.json")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"无法连接到原始服务 {ORIGINAL_API_URL}: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"获取 OpenAPI schema 失败: {e.response.status_code}")

def create_proxy_routes(app: FastAPI, openapi_schema: Dict[str, Any]):
    """根据 OpenAPI schema 创建代理路由"""
    paths = openapi_schema.get("paths", {})
    
    async def create_proxy_handler(method: str, path_template: str):
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
            if "authorization" in request.headers:
                headers["authorization"] = request.headers["authorization"]
            
            # 构建目标 URL，替换路径参数
            target_path = path_template
            path_params = request.path_params
            for param_name, param_value in path_params.items():
                target_path = target_path.replace(f"{{{param_name}}}", str(param_value))
            
            target_url = f"{ORIGINAL_API_URL}{target_path}"
            
            # 发送请求到原始服务
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.request(
                        method=method,
                        url=target_url,
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
                    raise HTTPException(status_code=502, detail=f"无法连接到原始服务: {e}")
        
        return handler
    
    # 为每个路径和方法创建路由
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

async def setup_mcp_proxy():
    """设置 MCP 代理服务器"""
    print("=" * 60)
    print("MCP 代理服务器设置")
    print("=" * 60)
    print(f"\n原始 API 服务: {ORIGINAL_API_URL}")
    print(f"MCP 服务器端口: {MCP_SERVER_PORT}")
    print()
    
    # 获取 OpenAPI schema
    print("正在获取 OpenAPI schema...")
    try:
        openapi_schema = await fetch_openapi_schema()
        print(f"✓ 成功获取 OpenAPI schema")
        print(f"  - 服务名称: {openapi_schema.get('info', {}).get('title', 'Unknown')}")
        print(f"  - 版本: {openapi_schema.get('info', {}).get('version', 'Unknown')}")
        print(f"  - 路径数量: {len(openapi_schema.get('paths', {}))}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n请确保：")
        print(f"  1. FastAPI 服务运行在 {ORIGINAL_API_URL}")
        print(f"  2. 服务可以访问 /openapi.json 端点")
        return None
    
    # 创建代理 FastAPI 应用
    print("\n正在创建代理应用...")
    proxy_app = FastAPI(
        title=f"MCP Proxy for {openapi_schema.get('info', {}).get('title', 'API')}",
        description=f"MCP 代理服务器，连接到 {ORIGINAL_API_URL}",
        version="1.0.0",
    )
    
    # 创建代理路由
    print("正在创建代理路由...")
    create_proxy_routes(proxy_app, openapi_schema)
    print("✓ 代理路由创建完成")
    
    # 创建 MCP 服务器
    print("\n正在创建 MCP 服务器...")
    try:
        # 使用自定义 HTTP 客户端连接到原始服务
        http_client = httpx.AsyncClient(
            base_url=ORIGINAL_API_URL,
            timeout=30.0,
        )
        
        mcp = FastApiMCP(
            proxy_app,
            name=f"MCP Proxy for {openapi_schema.get('info', {}).get('title', 'API')}",
            http_client=http_client,
        )
        
        mcp.mount_http()
        print("✓ MCP 服务器创建完成")
        print(f"\n🎉 MCP 服务器已启动！")
        print(f"   URL: http://localhost:{MCP_SERVER_PORT}/mcp")
        print(f"\n在 Cursor 中配置：")
        print(f'   "url": "http://localhost:{MCP_SERVER_PORT}/mcp"')
        
        return proxy_app
        
    except Exception as e:
        print(f"❌ 创建 MCP 服务器失败: {e}")
        return None

def main():
    """主函数"""
    proxy_app = asyncio.run(setup_mcp_proxy())
    
    if proxy_app:
        print("\n" + "=" * 60)
        print("启动 MCP 代理服务器...")
        print("=" * 60)
        print(f"\n按 Ctrl+C 停止服务器\n")
        
        import uvicorn
        uvicorn.run(proxy_app, host="0.0.0.0", port=MCP_SERVER_PORT)
    else:
        print("\n❌ 无法启动 MCP 代理服务器")

if __name__ == "__main__":
    main()

