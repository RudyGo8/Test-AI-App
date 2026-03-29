"""
=========================================================
测试AI应用 - 工具注册表
=========================================================
定义可用的工具:
1. playwright - 浏览器自动化
2. http_request - HTTP请求
3. file_writer - 文件操作
4. database - 数据库操作
5. calculator - 计算工具
=========================================================
"""

import asyncio
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表
    所有可用工具都在这里注册
    """
    
    _tools: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, name: str):
        """装饰器: 注册工具"""
        def decorator(func: Callable):
            cls._tools[name] = func
            logger.info(f"Registered tool: {name}")
            return func
        return decorator
    
    @classmethod
    def get_tool(cls, name: str) -> Callable:
        """获取工具"""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> list:
        """列出所有工具"""
        return list(cls._tools.keys())


@ToolRegistry.register('playwright_browser')
async def playwright_tool(params: Dict, context: Dict) -> Dict[str, Any]:
    """
    Playwright浏览器操作工具
    
    参数:
        action: 操作类型 (launch, goto, fill, click, screenshot, close)
        url: 页面URL
        selector: CSS选择器
        value: 输入值
        filename: 截图文件名
    """
    action = params.get('action', 'launch')
    
    if action == 'launch':
        browser_type = params.get('browser', 'chromium')
        return {
            'status': 'success',
            'message': f'{browser_type} browser launched',
            'browser_id': 'mock-browser-001'
        }
    
    elif action == 'goto':
        url = params.get('url', '')
        return {
            'status': 'success',
            'message': f'Navigated to {url}',
            'url': url
        }
    
    elif action == 'fill':
        selector = params.get('selector', '')
        value = params.get('value', '')
        return {
            'status': 'success',
            'message': f'Filled {selector} with {value}',
            'selector': selector
        }
    
    elif action == 'click':
        selector = params.get('selector', '')
        return {
            'status': 'success',
            'message': f'Clicked {selector}',
            'selector': selector
        }
    
    elif action == 'screenshot':
        filename = params.get('filename', 'screenshot.png')
        return {
            'status': 'success',
            'message': f'Screenshot saved: {filename}',
            'filename': filename,
            'path': f'/test-results/{filename}'
        }
    
    elif action == 'close':
        return {
            'status': 'success',
            'message': 'Browser closed'
        }
    
    return {'status': 'error', 'message': f'Unknown action: {action}'}


@ToolRegistry.register('http_request')
async def http_request_tool(params: Dict, context: Dict) -> Dict[str, Any]:
    """
    HTTP请求工具
    
    参数:
        url: 请求URL
        method: 请求方法 (GET, POST, PUT, DELETE)
        headers: 请求头
        body: 请求体
    """
    method = params.get('method', 'GET')
    url = params.get('url', '')
    
    return {
        'status': 'success',
        'message': f'{method} request to {url}',
        'response_code': 200,
        'response_body': {'result': 'success'}
    }


@ToolRegistry.register('file_writer')
async def file_writer_tool(params: Dict, context: Dict) -> Dict[str, Any]:
    """
    文件写入工具
    
    参数:
        path: 文件路径
        content: 文件内容
        mode: 写入模式 (w, a)
    """
    path = params.get('path', '')
    content = params.get('content', '')
    
    return {
        'status': 'success',
        'message': f'File written: {path}',
        'path': path,
        'size': len(content)
    }


@ToolRegistry.register('file_reader')
async def file_reader_tool(params: Dict, context: Dict) -> Dict[str, Any]:
    """
    文件读取工具
    
    参数:
        path: 文件路径
    """
    path = params.get('path', '')
    
    mock_content = f"Mock content of {path}"
    
    return {
        'status': 'success',
        'message': f'File read: {path}',
        'path': path,
        'content': mock_content
    }


@ToolRegistry.register('database_query')
async def database_tool(params: Dict, context: Dict) -> Dict[str, Any]:
    """
    数据库操作工具
    
    参数:
        operation: 操作类型 (query, insert, update, delete)
        table: 表名
        conditions: 查询条件
        data: 插入/更新的数据
    """
    operation = params.get('operation', 'query')
    table = params.get('table', '')
    
    return {
        'status': 'success',
        'message': f'Database {operation} on {table}',
        'rows_affected': 1,
        'data': [{'id': 1, 'name': 'test'}]
    }


@ToolRegistry.register('calculator')
async def calculator_tool(params: Dict, context: Dict) -> Dict[str, Any]:
    """
    计算工具
    
    参数:
        expression: 数学表达式
    """
    expression = params.get('expression', '0')
    
    try:
        result = eval(expression)
        return {
            'status': 'success',
            'expression': expression,
            'result': result
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Calculation error: {str(e)}'
        }


@ToolRegistry.register('assertion')
async def assertion_tool(params: Dict, context: Dict) -> Dict[str, Any]:
    """
    断言工具 - 用于验证测试结果
    
    参数:
        type: 断言类型 (equals, contains, exists, visible)
        actual: 实际值
        expected: 期望值
        selector: CSS选择器 (用于DOM断言)
    """
    assertion_type = params.get('type', 'equals')
    actual = params.get('actual')
    expected = params.get('expected')
    
    if assertion_type == 'equals':
        passed = actual == expected
    elif assertion_type == 'contains':
        passed = expected in str(actual)
    elif assertion_type == 'exists':
        passed = actual is not None
    else:
        passed = False
    
    return {
        'status': 'success',
        'assertion_type': assertion_type,
        'passed': passed,
        'expected': expected,
        'actual': actual
    }


class ToolExecutor:
    """
    工具执行器
    负责执行工具并记录日志
    """
    
    def __init__(self):
        self.execution_logs = []
    
    async def execute(self, tool_name: str, params: Dict, context: Dict) -> Dict:
        """执行工具"""
        log_entry = {
            'tool': tool_name,
            'params': params,
            'timestamp': None
        }
        
        tool_func = ToolRegistry.get_tool(tool_name)
        if not tool_func:
            result = {'status': 'error', 'message': f'Tool {tool_name} not found'}
        else:
            try:
                result = await tool_func(params, context)
            except Exception as e:
                result = {'status': 'error', 'message': str(e)}
        
        log_entry['result'] = result
        self.execution_logs.append(log_entry)
        
        return result
    
    def get_logs(self) -> list:
        """获取执行日志"""
        return self.execution_logs
