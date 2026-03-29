"""
=========================================================
测试AI应用 - 核心服务层
=========================================================
包含:
1. 任务分流服务 - IntentRoutingService
2. RAG检索服务 - RAGService  
3. 内容生成服务 - ContentGenerationService
4. 流程编排服务 - OrchestrationService
5. 工具调用服务 - ToolCallService
6. 结果回传服务 - ResultCallbackService
=========================================================
"""

import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class IntentRoutingService:
    """
    任务分流服务
    负责分析用户输入，判断意图并拆分子任务
    """

    INTENT_PATTERNS = {
        'generate_case': [
            '生成测试用例', '创建测试', '编写用例', '设计测试',
            'generate test case', 'create test', 'write test'
        ],
        'execute_test': [
            '执行测试', '跑测试', '运行测试', '测试一下',
            'execute test', 'run test', 'run automation'
        ],
        'query_knowledge': [
            '什么是', '怎么写', '如何做', '查询', '介绍',
            'what is', 'how to', 'explain'
        ],
        'generate_and_execute': [
            '生成测试用例，并执行', '创建并运行', '生成并执行自动化',
            'generate and execute', 'create and run test'
        ],
    }

    @classmethod
    def analyze_intent(cls, user_input: str) -> Dict[str, Any]:
        """
        分析用户意图
        
        Args:
            user_input: 用户输入
            
        Returns:
            {
                'intent': 'generate_case' | 'execute_test' | 'query_knowledge' | 'generate_and_execute' | 'general',
                'confidence': 0.95,
                'sub_tasks': [
                    {'task': 'generate_case', 'description': '生成测试用例'},
                    {'task': 'execute_test', 'description': '执行自动化测试'}
                ],
                'entities': {
                    'page_name': '登录页面',
                    'test_type': '功能测试'
                }
            }
        """
        user_input_lower = user_input.lower()
        
        matched_intents = []
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in user_input_lower:
                    matched_intents.append(intent)
                    break
        
        if 'generate_and_execute' in matched_intents:
            intent = 'generate_and_execute'
            sub_tasks = [
                {'task': 'generate_case', 'description': '生成测试用例'},
                {'task': 'execute_test', 'description': '执行自动化测试'}
            ]
        elif 'generate_case' in matched_intents:
            intent = 'generate_case'
            sub_tasks = [{'task': 'generate_case', 'description': '生成测试用例'}]
        elif 'execute_test' in matched_intents:
            intent = 'execute_test'
            sub_tasks = [{'task': 'execute_test', 'description': '执行自动化测试'}]
        elif 'query_knowledge' in matched_intents:
            intent = 'query_knowledge'
            sub_tasks = [{'task': 'query_knowledge', 'description': '查询知识库'}]
        else:
            intent = 'general'
            sub_tasks = [{'task': 'general', 'description': '一般对话'}]
        
        entities = cls._extract_entities(user_input)
        
        logger.info(f"Intent analyzed: {intent}, entities: {entities}")
        
        return {
            'intent': intent,
            'confidence': 0.9,
            'sub_tasks': sub_tasks,
            'entities': entities
        }

    @classmethod
    def _extract_entities(cls, user_input: str) -> Dict[str, str]:
        """提取实体"""
        entities = {}
        
        page_keywords = ['页面', '界面', 'screen', 'page']
        for keyword in page_keywords:
            if keyword in user_input:
                idx = user_input.find(keyword)
                entities['page_name'] = user_input[max(0, idx-10):idx+10]
                break
        
        test_types = ['功能测试', '边界值', '安全测试', '性能测试', 'functional', 'boundary']
        for test_type in test_types:
            if test_type in user_input:
                entities['test_type'] = test_type
                break
        
        return entities


class RAGService:
    """
    RAG检索增强服务
    负责从知识库检索相关信息
    """

    KNOWLEDGE_BASE = [
        {
            'id': 'kb001',
            'name': '登录功能测试用例模板',
            'content': '''
            登录功能测试用例模板:
            1. 用例名称: XXX登录功能测试
            2. 测试步骤:
               - 打开登录页面
               - 输入用户名
               - 输入密码
               - 点击登录按钮
               - 等待页面跳转
            3. 预期结果:
               - 成功: 跳转到首页，显示用户名
               - 失败: 显示错误提示信息
            4. 边界值:
               - 空用户名测试
               - 空密码测试
               - 错误密码测试
               - SQL注入测试
            ''',
            'type': 'template'
        },
        {
            'id': 'kb002',
            'name': '边界值测试方法',
            'content': '''
            边界值测试方法:
            - 等价类划分: 有效等价类和无效等价类
            - 边界值: 最小值、最大值、次小值、次大值
            - 常见边界: 0、1、空字符串、最大字符数
            - 数值边界: -1、0、1、max、max+1
            ''',
            'type': 'method'
        },
        {
            'id': 'kb003',
            'name': 'Playwright自动化测试',
            'content': '''
            Playwright自动化测试步骤:
            1. 安装: pip install playwright && playwright install chromium
            2. 初始化浏览器: browser = await playwright.chromium.launch()
            3. 创建页面: page = await browser.new_page()
            4. 导航: await page.goto("url")
            5. 操作: await page.fill(selector, value)
            6. 断言: expect(page).to_have_title()
            7. 截图: await page.screenshot()
            8. 关闭: await browser.close()
            ''',
            'type': 'tool'
        }
    ]

    @classmethod
    def retrieve(cls, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        检索知识库
        
        Args:
            query: 查询内容
            top_k: 返回数量
            
        Returns:
            [
                {
                    'id': 'kb001',
                    'name': '文档名称',
                    'content': '文档内容',
                    'type': 'template',
                    'similarity': 0.95
                },
                ...
            ]
        """
        results = []
        query_lower = query.lower()
        
        for kb in cls.KNOWLEDGE_BASE:
            score = cls._calculate_similarity(query_lower, kb['content'].lower())
            if score > 0.1:
                results.append({
                    'id': kb['id'],
                    'name': kb['name'],
                    'content': kb['content'],
                    'type': kb['type'],
                    'similarity': round(score, 3)
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]

    @classmethod
    def _calculate_similarity(cls, query: str, content: str) -> float:
        """简单计算相似度"""
        query_words = set(query.split())
        content_words = set(content.split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words & content_words
        return len(intersection) / len(query_words)


class ContentGenerationService:
    """
    内容生成服务
    负责生成测试用例、测试代码等内容
    """

    @classmethod
    def generate_test_case(cls, intent: Dict, knowledge_sources: List[Dict]) -> Dict[str, Any]:
        """
        生成测试用例
        
        Args:
            intent: 意图分析结果
            knowledge_sources: 检索到的知识
            
        Returns:
            {
                'case_name': '登录页面功能测试',
                'case_type': 'functional',
                'description': '测试登录功能是否正常',
                'preconditions': '用户已注册',
                'test_steps': [
                    {'step': 1, 'action': '打开登录页面', 'selector': '#login', 'value': ''},
                    {'step': 2, 'action': '输入用户名', 'selector': '#username', 'value': 'testuser'},
                    ...
                ],
                'expected_results': {
                    'url_contains': '/home',
                    'visible': ['#username-display']
                }
            }
        """
        entities = intent.get('entities', {})
        page_name = entities.get('page_name', '测试页面')
        test_type = entities.get('test_type', '功能测试')
        
        template = knowledge_sources[0] if knowledge_sources else {}
        
        case_name = f"{page_name}功能测试"
        
        if '边界' in test_type or 'boundary' in test_type.lower():
            case_type = 'boundary'
            test_steps = cls._generate_boundary_steps(page_name)
        else:
            case_type = 'functional'
            test_steps = cls._generate_functional_steps(page_name)
        
        return {
            'case_name': case_name,
            'case_type': case_type,
            'description': f'测试{page_name}的正常功能',
            'preconditions': '测试用户已注册，系统正常运行',
            'test_steps': test_steps,
            'expected_results': {
                'status_code': 200,
                'message': '操作成功'
            }
        }

    @classmethod
    def _generate_functional_steps(cls, page_name: str) -> List[Dict]:
        """生成功能测试步骤"""
        return [
            {'step': 1, 'action': '打开浏览器', 'type': 'browser', 'value': 'chromium'},
            {'step': 2, 'action': f'访问{page_name}', 'type': 'goto', 'value': 'http://example.com/login'},
            {'step': 3, 'action': '输入用户名', 'type': 'fill', 'selector': '#username', 'value': 'testuser'},
            {'step': 4, 'action': '输入密码', 'type': 'fill', 'selector': '#password', 'value': 'Test123456'},
            {'step': 5, 'action': '点击登录按钮', 'type': 'click', 'selector': '#login-btn'},
            {'step': 6, 'action': '等待页面跳转', 'type': 'wait', 'selector': '#home'},
            {'step': 7, 'action': '截图保存', 'type': 'screenshot', 'value': 'login_success.png'},
            {'step': 8, 'action': '关闭浏览器', 'type': 'close', 'value': ''},
        ]

    @classmethod
    def _generate_boundary_steps(cls, page_name: str) -> List[Dict]:
        """生成边界值测试步骤"""
        return [
            {'step': 1, 'action': '打开浏览器', 'type': 'browser', 'value': 'chromium'},
            {'step': 2, 'action': f'访问{page_name}', 'type': 'goto', 'value': 'http://example.com/login'},
            {'step': 3, 'action': '测试空用户名', 'type': 'fill', 'selector': '#username', 'value': ''},
            {'step': 4, 'action': '输入密码', 'type': 'fill', 'selector': '#password', 'value': 'Test123456'},
            {'step': 5, 'action': '点击登录', 'type': 'click', 'selector': '#login-btn'},
            {'step': 6, 'action': '验证错误提示', 'type': 'assert', 'selector': '.error-msg', 'value': '用户名不能为空'},
        ]


class OrchestrationService:
    """
    流程编排服务
    负责调度工具，按顺序执行任务
    """

    @classmethod
    async def execute_workflow(cls, workflow: List[Dict], context: Dict) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow: 工作流步骤列表
            context: 执行上下文
            
        Returns:
            {
                'status': 'success',
                'results': [...],
                'execution_time': 3.5
            }
        """
        results = []
        start_time = datetime.now()
        
        for step in workflow:
            step_name = step.get('name')
            tool_name = step.get('tool')
            params = step.get('params', {})
            
            logger.info(f"Executing step: {step_name}, tool: {tool_name}")
            
            result = await cls._execute_tool(tool_name, params, context)
            
            results.append({
                'step': step_name,
                'tool': tool_name,
                'status': 'success' if result.get('status') == 'success' else 'failed',
                'result': result
            })
            
            if result.get('status') == 'failed':
                break
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success' if all(r['status'] == 'success' for r in results) else 'failed',
            'results': results,
            'execution_time': execution_time
        }

    @classmethod
    async def _execute_tool(cls, tool_name: str, params: Dict, context: Dict) -> Dict:
        """执行单个工具"""
        from .tools import ToolRegistry
        
        tool_func = ToolRegistry.get_tool(tool_name)
        if tool_func:
            return await tool_func(params, context)
        else:
            return {'status': 'error', 'message': f'Tool {tool_name} not found'}


class ToolCallService:
    """
    工具调用服务
    负责执行具体的工具操作
    """

    @classmethod
    async def execute_tool(cls, tool_name: str, params: Dict, context: Dict) -> Dict:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            context: 上下文
            
        Returns:
            {
                'status': 'success',
                'data': {...}
            }
        """
        from .tools import ToolRegistry
        
        tool_func = ToolRegistry.get_tool(tool_name)
        if not tool_func:
            return {'status': 'error', 'message': f'Tool {tool_name} not found'}
        
        return await tool_func(params, context)


class ResultCallbackService:
    """
    结果回传服务
    负责将执行结果推送给用户
    """

    @classmethod
    async def notify(cls, task_id: str, result: Dict, callback_url: Optional[str] = None):
        """
        通知结果
        
        Args:
            task_id: 任务ID
            result: 执行结果
            callback_url: 回调URL
        """
        logger.info(f"Notifying result for task {task_id}")
        
        notification = {
            'task_id': task_id,
            'status': result.get('status'),
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        if callback_url:
            await cls._send_callback(callback_url, notification)
        
        return notification

    @classmethod
    async def _send_callback(cls, url: str, data: Dict):
        """发送回调"""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=data, timeout=10)
        except Exception as e:
            logger.error(f"Callback failed: {e}")
