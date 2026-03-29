from django.urls import path
from .views import (
    TestTaskAPIView,
    IntentAnalyzeAPIView,
    RAGRetrieveAPIView,
    TestCaseGenerateAPIView,
    TestExecuteAPIView,
    ToolCallAPIView,
    ToolsListAPIView,
    TaskHistoryAPIView,
)

urlpatterns = [
    # 主入口 - 完整业务流程
    path('task/', TestTaskAPIView.as_view(), name='test-ai-task'),
    
    # 意图分析
    path('analyze/', IntentAnalyzeAPIView.as_view(), name='test-ai-analyze'),
    
    # RAG检索
    path('retrieve/', RAGRetrieveAPIView.as_view(), name='test-ai-retrieve'),
    
    # 测试用例生成
    path('generate/', TestCaseGenerateAPIView.as_view(), name='test-ai-generate'),
    
    # 测试执行
    path('execute/', TestExecuteAPIView.as_view(), name='test-ai-execute'),
    
    # 工具调用
    path('tool/', ToolCallAPIView.as_view(), name='test-ai-tool'),
    
    # 工具列表
    path('tools/', ToolsListAPIView.as_view(), name='test-ai-tools'),
    
    # 任务历史
    path('history/', TaskHistoryAPIView.as_view(), name='test-ai-history'),
]
