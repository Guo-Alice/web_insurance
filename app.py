"""
养老金规划系统 - 修复Dify工作流输入格式问题版本
"""
from flask import Flask, render_template, request, jsonify, session
import os
import json
import requests
import traceback
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pension-planning-secret-key-2024")

# Dify配置
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "app-rd6ag4AYRsDqurCZ4KokIbNI")
WORKFLOW_ID = os.environ.get("WORKFLOW_ID", "bgvzc16WFu14fsnl")
DIFY_API_URL = "https://api.dify.ai/v1"

# ========== 修复Dify API调用 ==========
def call_dify_workflow(user_data):
    """
    调用Dify工作流API - 使用正确的输入格式
    """
    print(f"📤 调用Dify工作流 {WORKFLOW_ID}")
    
    # 检查配置
    if not DIFY_API_KEY or DIFY_API_KEY.startswith("app-xxx"):
        print("⚠️ API Key未配置，使用标准模型")
        return get_fallback_response(user_data, "API Key未配置")
    
    if not WORKFLOW_ID:
        print("⚠️ Workflow ID未配置，使用标准模型")
        return get_fallback_response(user_data, "Workflow ID未配置")
    
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 根据你的Dify工作流配置，输入变量名为"input"
    # 创建清晰的提示词格式
    prompt = f"""
用户养老金规划需求：
1. 年龄：{user_data.get('age')}岁
2. 年收入：{user_data.get('annual_income')}万元
3. 风险偏好：{user_data.get('risk_tolerance')}
4. 所在地区：{user_data.get('location', '全国')}
5. 社保类型：{user_data.get('social_security', '城镇职工')}
6. 计划退休年龄：{user_data.get('retirement_age', 60)}岁
7. 计划投资金额：{user_data.get('investment_amount', 10)}万元

请基于以上信息，提供一份全面的养老金规划建议。
"""
    
    payload = {
        "inputs": {
            "input": prompt.strip()  # 输入变量名为"input"
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    print(f"发送到Dify的payload: {json.dumps(payload, ensure_ascii=False)[:300]}...")
    
    try:
        response = requests.post(
            f"{DIFY_API_URL}/workflows/run",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Dify响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify工作流调用成功")
            print(f"响应结构: {list(result.keys())}")
            return extract_dify_response(result)
            
        elif response.status_code == 400:
            print(f"❌ Dify 400错误详情: {response.text[:500]}")
            # 尝试备选方案
            return call_dify_workflow_alternative(user_data, "400错误")
            
        else:
            print(f"❌ Dify API错误 {response.status_code}: {response.text[:200]}")
            return get_fallback_response(user_data, f"Dify API错误 {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Dify API超时")
        return get_fallback_response(user_data, "API超时")
    except Exception as e:
        print(f"❌ 调用Dify异常: {str(e)}")
        traceback.print_exc()
        return get_fallback_response(user_data, f"异常: {str(e)}")

def call_dify_workflow_alternative(user_data, error_reason):
    """备选方案 - 使用更简单的输入格式"""
    print("🔄 尝试备选输入格式...")
    
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 备选方案：使用更简单的文本格式
    simple_input = f"年龄{user_data.get('age')}岁 收入{user_data.get('annual_income')}万元 风险{user_data.get('risk_tolerance')} 地区{user_data.get('location')} 社保{user_data.get('social_security')} 退休{user_data.get('retirement_age')}岁 投资{user_data.get('investment_amount')}万元"
    
    payload = {
        "inputs": {
            "input": simple_input
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    print(f"备选方案payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{DIFY_API_URL}/workflows/run",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 备选方案调用成功")
            return extract_dify_response(result)
        else:
            print(f"❌ 备选方案失败: {response.status_code}")
            return get_fallback_response(user_data, f"Dify API错误 {response.status_code}（备选方案）")
            
    except Exception as e:
        print(f"❌ 备选方案异常: {str(e)}")
        return get_fallback_response(user_data, f"备选方案异常: {str(e)}")

def extract_dify_response(result):
    """提取Dify响应内容"""
    try:
        print(f"解析Dify响应，数据结构: {list(result.keys())}")
        
        # 检查是否有错误
        if 'error' in result:
            error_msg = result.get('error', {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get('message', '未知错误')
            return {
                "success": False,
                "answer": f"Dify错误: {error_msg}",
                "source": "Dify API错误"
            }
        
        # 尝试从不同位置提取响应
        if 'data' in result:
            data = result['data']
            
            # 检查 outputs
            if 'outputs' in data:
                outputs = data['outputs']
                print(f"找到outputs字段: {list(outputs.keys())}")
                
                # 尝试所有可能的输出键
                possible_keys = ['answer', 'output', 'response', 'text', 'content', 'result', 'report', 'pension_report', 'recommendation']
                for key in possible_keys:
                    if key in outputs and outputs[key]:
                        content = outputs[key]
                        if isinstance(content, dict):
                            # 如果是字典，转换为字符串
                            content = json.dumps(content, ensure_ascii=False, indent=2)
                        return {
                            "success": True,
                            "answer": str(content).strip(),
                            "source": "Dify AI工作流",
                            "raw_response": result
                        }
                
                # 如果没有找到标准键，尝试所有键
                for key in outputs.keys():
                    if outputs[key] and str(outputs[key]).strip():
                        return {
                            "success": True,
                            "answer": str(outputs[key]).strip(),
                            "source": "Dify AI工作流",
                            "raw_response": result
                        }
            
            # 如果直接有answer字段
            if 'answer' in data:
                return {
                    "success": True,
                    "answer": str(data['answer']).strip(),
                    "source": "Dify AI工作流",
                    "raw_response": result
                }
        
        # 如果没有找到预期的结构，检查是否有其他结构
        for key in ['answer', 'response', 'text', 'content', 'result', 'output']:
            if key in result and result[key]:
                return {
                    "success": True,
                    "answer": str(result[key]).strip(),
                    "source": "Dify AI工作流",
                    "raw_response": result
                }
        
        # 如果都没有找到，返回整个响应用于调试
        response_str = json.dumps(result, ensure_ascii=False, indent=2)
        return {
            "success": True,
            "answer": f"Dify工作流返回了数据，但格式不匹配。原始响应:\n\n{response_str}",
            "source": "Dify工作流（原始响应）",
            "raw_response": result
        }
        
    except Exception as e:
        print(f"解析Dify响应异常: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "answer": f"解析Dify响应失败: {str(e)}\n\n原始数据:\n{json.dumps(result, ensure_ascii=False)[:500]}",
            "source": "系统错误",
            "raw_response": result
        }

def get_fallback_response(user_data, error_reason=""):
    """回退响应"""
    advice = generate_standard_advice(user_data)
    
    response = {
        "success": True,
        "answer": advice,
        "source": "标准模型"
    }
    
    if error_reason:
        response["system_note"] = f"注：Dify AI服务暂时不可用（{error_reason}），已使用标准模型"
    
    return response

def generate_standard_advice(user_data):
    """生成标准养老金建议"""
    try:
        age = int(user_data.get('age', 30))
        income = float(user_data.get('annual_income', 20))
        risk = user_data.get('risk_tolerance', '平衡型')
        investment = float(user_data.get('investment_amount', 10))
        
        # 根据风险偏好确定资产配置
        if risk == '保守型':
            allocation = "银行存款(50%) + 国债(30%) + 货币基金(20%)"
            expected_return = "3-4%"
        elif risk == '稳健型':
            allocation = "债券基金(40%) + 年金保险(40%) + 平衡基金(20%)"
            expected_return = "4-6%"
        elif risk == '平衡型':
            allocation = "指数基金(40%) + 混合基金(30%) + 年金保险(30%)"
            expected_return = "6-8%"
        elif risk == '成长型':
            allocation = "股票基金(50%) + 指数基金(30%) + 年金保险(20%)"
            expected_return = "8-10%"
        else:  # 进取型
            allocation = "股票基金(60%) + 行业基金(30%) + 年金保险(10%)"
            expected_return = "10-12%"
        
        # 计算退休积蓄
        years_to_retire = max(1, 65 - age)
        monthly_saving = income * 0.15
        
        advice = f"""
🏦 智能养老金规划报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 客户基本信息
• 年龄：{age}岁
• 年收入：{income}万元
• 风险偏好：{risk}
• 计划投资金额：{investment}万元
• 预计退休年龄：{user_data.get('retirement_age', 60)}岁

📊 资产配置建议
根据您的风险偏好，推荐以下配置：
{allocation}

💰 预期收益分析
• 预计年化收益率：{expected_return}
• 每月建议储蓄：{monthly_saving:.1f}万元
• 退休前工作年限：{years_to_retire}年
• 退休时预计积累：{monthly_saving * 12 * years_to_retire * 1.5:.1f}万元

💡 专业建议
1. 尽早开始养老金规划，享受复利效应
2. 定期定额投资，降低市场波动风险
3. 每3-5年重新评估风险承受能力
4. 退休前10年逐步转为保守型配置

⚠️ 风险提示
投资有风险，以上建议仅供参考。具体投资决策请咨询专业理财顾问。
"""
        return advice
    except Exception as e:
        return f"生成建议时出错：{str(e)}"

# ========== Flask 路由 ==========
@app.route('/')
def index():
    """显示主页"""
    session.clear()
    session['session_id'] = str(uuid.uuid4())[:8]
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    """处理表单提交"""
    try:
        data = request.form.to_dict()
        print(f"📋 收到表单数据: {data}")
        
        # 基本验证
        required_fields = ['age', 'annual_income']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"请填写{'、'.join(missing_fields)}"
            })
        
        # 准备用户数据
        user_data = {
            "age": data.get('age', '30'),
            "annual_income": data.get('annual_income', '20'),
            "risk_tolerance": data.get('risk_tolerance', '平衡型'),
            "location": data.get('location', '全国'),
            "social_security": data.get('social_security', '城镇职工'),
            "retirement_age": data.get('retirement_age', '60'),
            "investment_amount": data.get('investment_amount', '10')
        }
        
        print(f"🤖 开始AI分析...")
        
        # 调用Dify工作流
        ai_result = call_dify_workflow(user_data)
        
        # 保存到session
        session['user_data'] = user_data
        session['ai_result'] = ai_result
        session['analysis_time'] = datetime.now().isoformat()
        
        # 构建返回结果
        response_data = {
            "success": True,
            "message": "分析完成！",
            "redirect": "/results",
            "ai_source": ai_result.get('source', '系统'),
            "system_note": ai_result.get('system_note', '')
        }
        
        # 如果是Dify响应，添加一些调试信息
        if ai_result.get('source', '').startswith('Dify'):
            response_data["debug"] = {
                "dify_success": ai_result.get('success'),
                "answer_length": len(str(ai_result.get('answer', ''))),
                "raw_keys": list(ai_result.get('raw_response', {}).keys()) if ai_result.get('raw_response') else []
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"🔥 表单提交异常: {str(e)}")
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "message": "系统繁忙，请稍后重试"
        })

@app.route('/results')
def show_results():
    """显示结果页面"""
    if 'user_data' not in session:
        return """
        <html>
        <head>
            <title>错误</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-warning">
                    <h4>请先提交表单</h4>
                    <p>您还没有提交养老金规划信息。</p>
                    <a href="/" class="btn btn-primary">返回首页填写信息</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    user_data = session.get('user_data', {})
    ai_result = session.get('ai_result', {})
    analysis_time = session.get('analysis_time', '')
    
    # 格式化时间
    if analysis_time:
        try:
            dt = datetime.fromisoformat(analysis_time.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y年%m月%d日 %H:%M:%S')
        except:
            formatted_time = analysis_time
    else:
        formatted_time = "未知时间"
    
    # 提取报告内容
    report = ai_result.get('answer', '未获取到分析结果')
    if not report or report.strip() == '':
        report = "系统未能生成分析结果，请重新提交或联系客服。"
    
    return render_template('results.html', 
                         user_data=user_data,
                         report=report,
                         source=ai_result.get('source', '标准模型'),
                         system_note=ai_result.get('system_note', ''),
                         analysis_time=formatted_time)

# ========== API 端点 ==========
@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "养老金规划系统",
        "timestamp": datetime.now().isoformat(),
        "dify_configured": bool(DIFY_API_KEY and not DIFY_API_KEY.startswith("app-xxx")),
        "workflow_configured": bool(WORKFLOW_ID)
    })

@app.route('/api/test-workflow')
def test_workflow():
    """测试工作流调用"""
    test_data = {
        "age": "35",
        "annual_income": "25.0",
        "risk_tolerance": "平衡型",
        "location": "北京",
        "social_security": "城镇职工",
        "retirement_age": "60",
        "investment_amount": "12.0"
    }
    
    result = call_dify_workflow(test_data)
    
    return jsonify({
        "test_time": datetime.now().isoformat(),
        "test_data": test_data,
        "test_result": {
            "success": result.get('success', False),
            "source": result.get('source', '未知'),
            "answer_preview": str(result.get('answer', ''))[:200] + "..." if result.get('answer') else "无内容",
            "system_note": result.get('system_note', '')
        },
        "dify_config": {
            "api_key_configured": bool(DIFY_API_KEY and not DIFY_API_KEY.startswith("app-xxx")),
            "workflow_id": WORKFLOW_ID,
            "api_url": DIFY_API_URL
        }
    })

@app.route('/api/dify-debug')
def dify_debug():
    """Dify调试接口"""
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 多个测试用例
    test_cases = [
        {
            "name": "简单测试",
            "input": "你好，请帮我规划养老金"
        },
        {
            "name": "基本数据测试",
            "input": "年龄35岁，收入25万元，风险平衡型"
        },
        {
            "name": "详细数据测试",
            "input": "用户年龄35岁，年收入25万元，风险偏好平衡型，所在地北京，社保类型城镇职工，计划60岁退休，计划投资12万元。请提供养老金规划建议。"
        }
    ]
    
    results = []
    
    for test in test_cases:
        payload = {
            "inputs": {
                "input": test["input"]
            },
            "response_mode": "blocking",
            "user": "user_test"
        }
        
        try:
            response = requests.post(
                f"{DIFY_API_URL}/workflows/run",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            result = {
                "test_name": test["name"],
                "status_code": response.status_code,
                "input": test["input"]
            }
            
            if response.status_code == 200:
                response_json = response.json()
                result["response"] = response_json
                
                # 提取可能的输出
                if 'data' in response_json and 'outputs' in response_json['data']:
                    outputs = response_json['data']['outputs']
                    result["output_keys"] = list(outputs.keys())
                    
                    for key in ['answer', 'output', 'response', 'text']:
                        if key in outputs and outputs[key]:
                            result["output_preview"] = str(outputs[key])[:200]
                            break
            else:
                result["error"] = response.text[:500]
                
        except Exception as e:
            result = {
                "test_name": test["name"],
                "error": str(e),
                "status_code": 0
            }
        
        results.append(result)
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "workflow_id": WORKFLOW_ID,
        "api_key_configured": bool(DIFY_API_KEY and not DIFY_API_KEY.startswith("app-xxx")),
        "test_results": results
    })

# ========== 错误处理 ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "404 Not Found",
        "message": "请求的URL不存在",
        "suggestion": "请检查URL或访问主页"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"🔥 500错误详情: {str(error)}")
    traceback.print_exc()
    
    return jsonify({
        "error": "500 Internal Server Error",
        "message": "服务器内部错误",
        "suggestion": "请刷新页面重试，或联系技术支持"
    }), 500

# ========== 启动应用 ==========
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 60)
    print("养老金规划系统启动")
    print(f"Dify API配置: {'✅ 已配置' if DIFY_API_KEY and not DIFY_API_KEY.startswith('app-xxx') else '❌ 未配置'}")
    print(f"工作流ID: {'✅ ' + WORKFLOW_ID if WORKFLOW_ID else '❌ 未配置'}")
    print(f"本地访问: http://localhost:{port}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    application = app
