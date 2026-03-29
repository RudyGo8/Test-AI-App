import requests
import json

BASE_URL = "http://localhost:8000"

def test_tools_list():
    """测试获取工具列表"""
    response = requests.get(f"{BASE_URL}/api/test-ai/tools/")
    print(f"[GET] /api/test-ai/tools/ - {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response

def test_analyze():
    """测试意图分析"""
    data = {"user_input": "帮我生成登录页面的测试用例"}
    response = requests.post(f"{BASE_URL}/api/test-ai/analyze/", json=data)
    print(f"\n[POST] /api/test-ai/analyze/ - {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response

def test_retrieve():
    """测试RAG检索"""
    data = {"query": "什么是边界值测试"}
    response = requests.post(f"{BASE_URL}/api/test-ai/retrieve/", json=data)
    print(f"\n[POST] /api/test-ai/retrieve/ - {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response

def test_generate():
    """测试测试用例生成"""
    data = {"user_input": "为登录页面生成测试用例"}
    response = requests.post(f"{BASE_URL}/api/test-ai/generate/", json=data)
    print(f"\n[POST] /api/test-ai/generate/ - {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response

def test_full_task():
    """测试完整业务流程"""
    data = {"user_input": "帮我为一个登录页面生成测试用例，并执行自动化测试"}
    response = requests.post(f"{BASE_URL}/api/test-ai/task/", json=data)
    print(f"\n[POST] /api/test-ai/task/ - {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response

def test_history():
    """测试任务历史"""
    response = requests.get(f"{BASE_URL}/api/test-ai/history/")
    print(f"\n[GET] /api/test-ai/history/ - {response.status_code}")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response


if __name__ == "__main__":
    print("=" * 50)
    print("测试工具列表")
    print("=" * 50)
    test_tools_list()

    print("\n" + "=" * 50)
    print("测试意图分析")
    print("=" * 50)
    test_analyze()

    print("\n" + "=" * 50)
    print("测试RAG检索")
    print("=" * 50)
    test_retrieve()

    print("\n" + "=" * 50)
    print("测试测试用例生成")
    print("=" * 50)
    test_generate()

    print("\n" + "=" * 50)
    print("测试完整业务流程")
    print("=" * 50)
    test_full_task()

    print("\n" + "=" * 50)
    print("测试任务历史")
    print("=" * 50)
    test_history()
