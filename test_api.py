#!/usr/bin/env python3
"""
测试增强的API功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_system_status():
    """测试系统状态API"""
    print("🔍 测试系统状态API...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/system/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统状态API正常")
            print(f"   状态: {data['status']}")
            print(f"   已加载模型: {data['data']['models']['models_loaded']}")
            print(f"   处理器状态: {data['data']['processor_status']}")
        else:
            print(f"❌ 系统状态API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 系统状态API异常: {e}")

def test_model_performance():
    """测试模型性能API"""
    print("\n🤖 测试模型性能API...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/models/performance")
        if response.status_code == 200:
            data = response.json()
            print("✅ 模型性能API正常")
            for model_name, metrics in data['data']['metrics'].items():
                print(f"   {model_name}: CV得分 {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
        else:
            print(f"❌ 模型性能API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 模型性能API异常: {e}")

def test_risk_assessment():
    """测试风险评估API"""
    print("\n🩺 测试风险评估API...")
    try:
        # 准备测试数据
        payload = {
            "age": 45,
            "bmi": 24.5,
            "smoking": False,
            "alcohol": False,
            "family_history": True,
            "symptom_score": 3,
            "lab_cea": 3.2,
            "lab_ca125": 25.0
        }
        
        # 发送请求
        files = {'payload': (None, json.dumps(payload))}
        response = requests.post(f"{BASE_URL}/api/v1/assess", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 风险评估API正常")
            print(f"   风险分值: {data['risk_score']:.4f}")
            print(f"   风险等级: {data['risk_level']}")
            print(f"   置信度: {data['confidence']:.4f}")
            detailed_text = str(data['detailed_analysis'])
            print(f"   详细分析: {detailed_text[:100]}...")
            print(f"   建议数量: {len(data['recommendations'])}")
        else:
            print(f"❌ 风险评估API失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 风险评估API异常: {e}")

def test_batch_assessment():
    """测试批量评估API"""
    print("\n📊 测试批量评估API...")
    try:
        # 准备批量测试数据
        patients = [
            {
                "name": "患者1",
                "age": 45,
                "bmi": 24.5,
                "smoking": False,
                "alcohol": False,
                "family_history": True,
                "symptom_score": 3,
                "lab_cea": 3.2,
                "lab_ca125": 25.0
            },
            {
                "name": "患者2", 
                "age": 55,
                "bmi": 28.0,
                "smoking": True,
                "alcohol": True,
                "family_history": False,
                "symptom_score": 5,
                "lab_cea": 5.5,
                "lab_ca125": 35.0
            }
        ]
        
        response = requests.post(f"{BASE_URL}/api/v1/assess/batch", json={"patients": patients})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 批量评估API正常")
            results = data['data']['results']
            summary = data['data']['summary']
            print(f"   处理患者数: {summary['total_patients']}")
            print(f"   成功评估数: {summary['successful_assessments']}")
            print(f"   高风险患者数: {summary['high_risk_patients']}")
            for i, result in enumerate(results):
                if 'error' not in result:
                    print(f"   患者{i+1}: 风险分值 {result['risk_score']:.4f}, 等级 {result['risk_level']}")
                else:
                    print(f"   患者{i+1}: 评估失败 - {result['error']}")
        else:
            print(f"❌ 批量评估API失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
    except Exception as e:
        print(f"❌ 批量评估API异常: {e}")

def main():
    print("🚀 开始测试增强的API功能\n")
    
    # 测试各个API端点
    test_system_status()
    test_model_performance()
    test_risk_assessment()
    test_batch_assessment()
    
    print("\n✨ API测试完成!")

if __name__ == "__main__":
    main()