from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TestTask(models.Model):
    """
    测试任务模型 - 记录完整的测试业务流程
    """
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('analyzing', '分析中'),
        ('generating', '生成中'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    INTENT_CHOICES = [
        ('generate_case', '生成测试用例'),
        ('execute_test', '执行测试'),
        ('query_knowledge', '知识查询'),
        ('generate_and_execute', '生成并执行'),
        ('general', '一般对话'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_tasks')
    session_id = models.CharField(max_length=64, db_index=True)
    
    user_input = models.TextField(verbose_name='用户输入')
    intent = models.CharField(max_length=32, choices=INTENT_CHOICES, verbose_name='识别意图')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    generated_case = models.JSONField(null=True, blank=True, verbose_name='生成的测试用例')
    execution_result = models.JSONField(null=True, blank=True, verbose_name='执行结果')
    
    rag_sources = models.JSONField(null=True, blank=True, verbose_name='RAG检索来源')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_ai_task'
        ordering = ['-created_at']
        verbose_name = '测试任务'
        verbose_name_plural = '测试任务'

    def __str__(self):
        return f"{self.id} - {self.intent} - {self.status}"


class TestCase(models.Model):
    """
    测试用例模型 - 存储生成的测试用例
    """
    TYPE_CHOICES = [
        ('functional', '功能测试'),
        ('boundary', '边界值测试'),
        ('security', '安全测试'),
        ('performance', '性能测试'),
    ]

    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name='test_cases')
    case_name = models.CharField(max_length=255, verbose_name='用例名称')
    case_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='用例类型')
    description = models.TextField(verbose_name='用例描述')
    preconditions = models.TextField(verbose_name='前置条件')
    test_steps = models.JSONField(verbose_name='测试步骤')
    expected_results = models.JSONField(verbose_name='预期结果')
    
    execution_status = models.CharField(max_length=20, null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True, verbose_name='执行时长(秒)')
    execution_logs = models.TextField(null=True, blank=True, verbose_name='执行日志')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'test_ai_case'
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例'

    def __str__(self):
        return self.case_name


class KnowledgeSource(models.Model):
    """
    知识来源 - RAG检索的知识库
    """
    name = models.CharField(max_length=255, verbose_name='知识名称')
    content = models.TextField(verbose_name='知识内容')
    content_type = models.CharField(max_length=50, verbose_name='内容类型')
    similarity = models.FloatField(null=True, blank=True, verbose_name='相似度')
    
    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name='knowledge_sources')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'test_ai_knowledge'
        verbose_name = '知识来源'
        verbose_name_plural = '知识来源'

    def __str__(self):
        return f"{self.name} ({self.similarity:.2f})"
