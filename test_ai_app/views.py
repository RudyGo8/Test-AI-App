"""
=========================================================
测试AI应用 - API视图
=========================================================
主要入口:
1. TestTaskAPIView - 主入口，处理完整业务流程
2. IntentAnalyzeAPIView - 意图分析
3. RAGRetrieveAPIView - 知识检索
4. TestCaseGenerateAPIView - 测试用例生成
5. TestExecuteAPIView - 测试执行
6. ToolCallAPIView - 工具调用
=========================================================
"""

import uuid
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import TestTask, TestCase, KnowledgeSource
from .services import (
    IntentRoutingService,
    RAGService,
    ContentGenerationService,
    OrchestrationService,
    ToolCallService,
    ResultCallbackService
)
from .tools import ToolRegistry

logger = logging.getLogger(__name__)


class TestTaskAPIView(APIView):
    """
    =========================================================
    主入口: 测试任务API
    路由: POST /api/test-ai/task/
    =========================================================
    
    完整业务流程:
    1. 任务分流 - 分析用户意图
    2. RAG检索 - 查询知识库
    3. 内容生成 - 生成测试用例
    4. 流程编排 - 编排执行步骤
    5. 工具调用 - 执行自动化
    6. 结果回传 - 返回结果
    
    请求:
    {
        "user_input": "帮我为一个登录页面生成测试用例，并执行自动化测试",
        "callback_url": "可选，回调通知地址"
    }
    
    响应:
    {
        "status": "success",
        "task_id": "xxx",
        "intent": "generate_and_execute",
        "generated_case": {...},
        "execution_result": {...},
        "rag_sources": [...]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_input = request.data.get('user_input', '')
        callback_url = request.data.get('callback_url')
        
        if not user_input:
            return Response({
                'status': 'error',
                'message': 'user_input is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        session_id = request.data.get('session_id', uuid.uuid4().hex)
        
        task = TestTask.objects.create(
            user=request.user,
            session_id=session_id,
            user_input=user_input,
            status='analyzing'
        )
        
        try:
            result = self._execute_workflow(task, user_input, callback_url)
            
            task.status = 'completed'
            task.execution_result = result
            task.save()
            
            return Response({
                'status': 'success',
                'task_id': str(task.id),
                'session_id': session_id,
                'intent': task.intent,
                'generated_case': task.generated_case,
                'execution_result': result,
                'rag_sources': task.rag_sources
            })
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = 'failed'
            task.save()
            
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _execute_workflow(self, task: TestTask, user_input: str, callback_url: str):
        """执行完整工作流"""
        result = {}
        
        step1_intent = IntentRoutingService.analyze_intent(user_input)
        task.intent = step1_intent['intent']
        task.status = 'generating'
        task.save()
        
        result['intent_analysis'] = step1_intent
        
        step2_rag = RAGService.retrieve(user_input, top_k=3)
        task.rag_sources = step2_rag
        task.save()
        
        for source in step2_rag:
            KnowledgeSource.objects.create(
                task=task,
                name=source['name'],
                content=source['content'],
                content_type=source['type'],
                similarity=source['similarity']
            )
        
        result['rag_results'] = step2_rag
        
        if step1_intent['intent'] in ['generate_case', 'generate_and_execute']:
            step3_case = ContentGenerationService.generate_test_case(
                step1_intent, step2_rag
            )
            task.generated_case = step3_case
            
            test_case = TestCase.objects.create(
                task=task,
                case_name=step3_case['case_name'],
                case_type=step3_case['case_type'],
                description=step3_case['description'],
                preconditions=step3_case['preconditions'],
                test_steps=step3_case['test_steps'],
                expected_results=step3_case['expected_results']
            )
            
            result['generated_case'] = step3_case
        
        if step1_intent['intent'] in ['execute_test', 'generate_and_execute']:
            task.status = 'executing'
            task.save()
            
            workflow = self._build_workflow(step1_intent, task.generated_case)
            
            import asyncio
            step4_execution = asyncio.run(
                OrchestrationService.execute_workflow(workflow, {})
            )
            
            test_case.execution_status = step4_execution['status']
            test_case.execution_time = step4_execution['execution_time']
            test_case.execution_logs = str(step4_execution)
            test_case.save()
            
            result['execution_result'] = step4_execution
        
        if callback_url:
            import asyncio
            asyncio.run(ResultCallbackService.notify(
                str(task.id), result, callback_url
            ))
        
        return result

    def _build_workflow(self, intent: dict, test_case: dict) -> list:
        """构建执行工作流"""
        workflow = []
        
        if test_case and 'test_steps' in test_case:
            for step in test_case['test_steps']:
                step_type = step.get('type', 'unknown')
                
                if step_type == 'browser':
                    workflow.append({
                        'name': f"Step {step['step']}: {step['action']}",
                        'tool': 'playwright_browser',
                        'params': {'action': 'launch', 'browser': step.get('value', 'chromium')}
                    })
                elif step_type == 'goto':
                    workflow.append({
                        'name': f"Step {step['step']}: {step['action']}",
                        'tool': 'playwright_browser',
                        'params': {'action': 'goto', 'url': step.get('value', '')}
                    })
                elif step_type == 'fill':
                    workflow.append({
                        'name': f"Step {step['step']}: {step['action']}",
                        'tool': 'playwright_browser',
                        'params': {'action': 'fill', 'selector': step.get('selector', ''), 'value': step.get('value', '')}
                    })
                elif step_type == 'click':
                    workflow.append({
                        'name': f"Step {step['step']}: {step['action']}",
                        'tool': 'playwright_browser',
                        'params': {'action': 'click', 'selector': step.get('selector', '')}
                    })
                elif step_type == 'screenshot':
                    workflow.append({
                        'name': f"Step {step['step']}: {step['action']}",
                        'tool': 'playwright_browser',
                        'params': {'action': 'screenshot', 'filename': step.get('value', 'screenshot.png')}
                    })
                elif step_type == 'close':
                    workflow.append({
                        'name': f"Step {step['step']}: {step['action']}",
                        'tool': 'playwright_browser',
                        'params': {'action': 'close'}
                    })
                elif step_type == 'assert':
                    workflow.append({
                        'name': f"Step {step['step']}: {step['action']}",
                        'tool': 'assertion',
                        'params': {
                            'type': 'equals',
                            'expected': step.get('value', ''),
                            'actual': 'mock_actual_value'
                        }
                    })
        
        return workflow


class IntentAnalyzeAPIView(APIView):
    """
    =========================================================
    入口: 意图分析
    路由: POST /api/test-ai/analyze/
    =========================================================
    """
    
    def post(self, request):
        user_input = request.data.get('user_input', '')
        
        if not user_input:
            return Response({
                'status': 'error',
                'message': 'user_input is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = IntentRoutingService.analyze_intent(user_input)
        
        return Response({
            'status': 'success',
            'data': result
        })


class RAGRetrieveAPIView(APIView):
    """
    =========================================================
    入口: RAG知识检索
    路由: POST /api/test-ai/retrieve/
    =========================================================
    """
    
    def post(self, request):
        query = request.data.get('query', '')
        top_k = request.data.get('top_k', 3)
        
        if not query:
            return Response({
                'status': 'error',
                'message': 'query is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = RAGService.retrieve(query, top_k)
        
        return Response({
            'status': 'success',
            'data': {
                'query': query,
                'results': results,
                'count': len(results)
            }
        })


class TestCaseGenerateAPIView(APIView):
    """
    =========================================================
    入口: 测试用例生成
    路由: POST /api/test-ai/generate/
    =========================================================
    """
    
    def post(self, request):
        user_input = request.data.get('user_input', '')
        
        if not user_input:
            return Response({
                'status': 'error',
                'message': 'user_input is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        intent = IntentRoutingService.analyze_intent(user_input)
        knowledge_sources = RAGService.retrieve(user_input, top_k=3)
        
        test_case = ContentGenerationService.generate_test_case(
            intent, knowledge_sources
        )
        
        return Response({
            'status': 'success',
            'data': {
                'intent': intent,
                'test_case': test_case,
                'knowledge_sources': knowledge_sources
            }
        })


class TestExecuteAPIView(APIView):
    """
    =========================================================
    入口: 测试执行
    路由: POST /api/test-ai/execute/
    =========================================================
    """
    
    def post(self, request):
        test_case = request.data.get('test_case', {})
        
        if not test_case:
            return Response({
                'status': 'error',
                'message': 'test_case is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        workflow = self._build_workflow(test_case)
        
        import asyncio
        result = asyncio.run(
            OrchestrationService.execute_workflow(workflow, {})
        )
        
        return Response({
            'status': 'success',
            'data': result
        })
    
    def _build_workflow(self, test_case: dict) -> list:
        workflow = []
        for step in test_case.get('test_steps', []):
            step_type = step.get('type', 'unknown')
            
            if step_type in ['browser', 'goto', 'fill', 'click', 'screenshot', 'close']:
                workflow.append({
                    'name': f"Step {step['step']}: {step['action']}",
                    'tool': 'playwright_browser',
                    'params': {'action': step_type if step_type != 'browser' else 'launch', 
                              'url' if step_type == 'goto' else 'selector' if step_type in ['fill', 'click'] else 'filename': 
                              step.get('value', '') if step_type == 'goto' else step.get('selector', '') if step_type in ['fill', 'click'] else step.get('value', '')}
                })
            elif step_type == 'assert':
                workflow.append({
                    'name': f"Step {step['step']}: {step['action']}",
                    'tool': 'assertion',
                    'params': {'type': 'equals', 'expected': step.get('value', ''), 'actual': 'mock'}
                })
        
        return workflow


class ToolCallAPIView(APIView):
    """
    =========================================================
    入口: 工具调用
    路由: POST /api/test-ai/tool/
    =========================================================
    """
    
    def post(self, request):
        tool_name = request.data.get('tool_name', '')
        params = request.data.get('params', {})
        
        if not tool_name:
            return Response({
                'status': 'error',
                'message': 'tool_name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        available_tools = ToolRegistry.list_tools()
        
        if tool_name not in available_tools:
            return Response({
                'status': 'error',
                'message': f'Tool {tool_name} not found',
                'available_tools': available_tools
            }, status=status.HTTP_404_NOT_FOUND)
        
        import asyncio
        result = asyncio.run(
            ToolCallService.execute_tool(tool_name, params, {})
        )
        
        return Response({
            'status': 'success',
            'data': result
        })


class ToolsListAPIView(APIView):
    """
    =========================================================
    入口: 工具列表
    路由: GET /api/test-ai/tools/
    =========================================================
    """
    
    def get(self, request):
        tools = ToolRegistry.list_tools()
        
        return Response({
            'status': 'success',
            'data': {
                'tools': tools,
                'count': len(tools)
            }
        })


class TaskHistoryAPIView(APIView):
    """
    =========================================================
    入口: 任务历史
    路由: GET /api/test-ai/history/
    =========================================================
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tasks = TestTask.objects.filter(user=request.user)[:10]
        
        return Response({
            'status': 'success',
            'data': [{
                'id': str(t.id),
                'user_input': t.user_input,
                'intent': t.intent,
                'status': t.status,
                'created_at': t.created_at.isoformat()
            } for t in tasks]
        })
