"""
养老金规划系统 - 修复版（适配Dify单输入工作流）
修复500错误，确保应用可用
"""
from flask import Flask, render_template, request, jsonify, session
import os
import json
import requests
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pension-planning-secret-key-2024")

# Dify配置
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "app-rd6ag4AYRsDqurCZ4KokIbNI")
WORKFLOW_ID = os.environ.get("WORKFLOW_ID", "bgvzc16WFu14fsnl")  # 注意：字母l
DIFY_API_URL = "https://api.dify.ai/v1"

# ========== Dify工作流调用函数 ==========
def call_dify_workflow(user_data):
    """
    调用Dify工作流API - 适配单个input字段
    """
    print(f"调用Dify工作流，用户年龄: {user_data.get('age')}")
    
    # 检查配置
    if not DIFY_API_KEY or DIFY_API_KEY.startswith("app-xxx"):
        print("⚠️ Dify API Key未配置，使用标准模型")
        return get_fallback_response(user_data, "API Key未配置")
    
    if not WORKFLOW_ID:
        print("⚠️ Workflow ID未配置，使用标准模型")
        return get_fallback_response(user_data, "Workflow ID未配置")
    
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 关键：将用户数据转换为字符串，作为input字段的值
    # 方法1：JSON格式（结构清晰）
    input_string = json.dumps(user_data, ensure_ascii=False, indent=2)
    
    # 方法2：自然语言格式（可选，根据您的工作流需求选择）
    # input_string = f"""用户养老金规划信息：
    # 年龄：{user_data.get('age')}岁
    # 年收入：{user_data.get('annual_income')}万元
    # 风险偏好：{user_data.get('risk_tolerance')}
    # 所在地区：{user_data.get('location')}
    # 社保类型：{user_data.get('social_security')}
    # 计划退休年龄：{user_data.get('retirement_age')}岁
    # 计划投资金额：{user_data.get('investment_amount')}万元"""
    
    payload = {
        "inputs": {
            "input": input_string  # 单个input字段
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    print(f"发送到Dify工作流的数据: {json.dumps(payload, ensure_ascii=False)[:500]}...")
    
    try:
        response = requests.post(
            f"{DIFY_API_URL}/workflows/run",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Dify响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify工作流调用成功")
            
            # 提取响应
            if 'data' in result and 'outputs' in result['data']:
                outputs = result['data']['outputs']
                
                # 尝试不同的输出字段名
                answer = ""
                possible_output_keys = ['output', 'answer', 'response', 'text', 'content', 'result']
                
                for key in possible_output_keys:
                    if key in outputs:
                        answer = outputs[key]
                        break
                
                if not answer:
                    # 如果没有找到标准字段，返回整个outputs
                    answer = json.dumps(outputs, ensure_ascii=False, indent=2)
                
                return {
                    "success": True,
                    "answer": answer,
                    "source": "Dify AI工作流"
                }
            else:
                return {
                    "success": True,
                    "answer": json.dumps(result, ensure_ascii=False, indent=2),
                    "source": "Dify工作流（原始响应）"
                }
        
        else:
            print(f"❌ Dify错误 {response.status_code}: {response.text[:200]}")
            return get_fallback_response(user_data, f"Dify API错误 {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Dify API超时")
        return get_fallback_response(user_data, "API超时")
    except Exception as e:
        print(f"❌ 调用Dify异常: {str(e)}")
        return get_fallback_response(user_data, f"异常: {str(e)}")

def get_fallback_response(user_data, error_reason=""):
    """回退响应，确保应用可用"""
    age = user_data.get('age', 30)
    income = user_data.get('annual_income', 20)
    risk = user_data.get('risk_tolerance', '平衡型')
    
    # 生成标准建议
    recommendations = [
        f"👤 **用户信息分析**",
        f"• 年龄：{age}岁",
        f"• 年收入：{income}万元",
        f"• 风险偏好：{risk}",
        "",
        f"📊 **养老金规划建议**",
        f"1. **资产配置方案**",
        f"   - 稳健型年金保险：40%",
        f"   - 平衡型基金组合：40%",
        f"   - 货币基金/存款：20%",
        "",
        f"2. **投资策略**",
        f"   - 每月定投金额：{float(income) * 0.12:.1f}万元（收入的12%）",
        f"   - 投资期限：{65 - int(age)}年",
        f"   - 年化预期收益：{get_expected_return(risk)}%",
        "",
        f"3. **风险提示**",
        f"   - 市场有风险，投资需谨慎",
        f"   - 建议每年进行一次投资组合评估",
        f"   - 退休前5年逐步增加保守型资产比例"
    ]
    
    if error_reason:
        recommendations.insert(0, f"⚠️ **系统提示**：{error_reason}，已使用标准模型为您生成建议。")
    
    return {
        "success": True,
        "answer": "\n".join(recommendations),
        "source": "标准模型"
    }

def get_expected_return(risk_tolerance):
    """根据风险偏好计算预期年化收益"""
    returns = {
        '保守型': 3.5,
        '稳健型': 5.0,
        '平衡型': 6.5,
        '成长型': 8.0,
        '进取型': 10.0
    }
    return returns.get(risk_tolerance, 5.0)

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
        print(f"收到表单数据: {data}")
        
        # 验证必需字段
        if not data.get('age'):
            return jsonify({"success": False, "message": "请填写年龄"})
        if not data.get('annual_income'):
            return jsonify({"success": False, "message": "请填写年收入"})
        
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
        
        print(f"调用AI分析...")
        
        # 调用Dify工作流
        ai_result = call_dify_workflow(user_data)
        
        # 保存到session
        session['user_data'] = user_data
        session['ai_result'] = ai_result
        session['analysis_time'] = datetime.now().isoformat()
        
        # 检查AI调用是否成功
        if not ai_result.get('success', True):
            return jsonify({
                "success": False,
                "message": f"AI分析失败: {ai_result.get('error', '未知错误')}"
            })
        
        return jsonify({
            "success": True,
            "message": "分析完成！",
            "redirect": "/results",
            "ai_source": ai_result.get('source', '系统')
        })
        
    except Exception as e:
        print(f"表单提交异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"服务器错误: {str(e)}"
        })

@app.route('/results')
def show_results():
    """显示结果页面"""
    if 'user_data' not in session:
        return render_template('error.html', message="请先提交表单")
    
    user_data = session.get('user_data', {})
    ai_result = session.get('ai_result', {})
    
    # 提取报告内容
    report = ai_result.get('answer', '未获取到分析结果')
    if not report or report.strip() == '':
        report = "AI未生成有效内容，请重新提交"
    
    return render_template('results.html', 
                         user_data=user_data,
                         report=report,
                         source=ai_result.get('source', '标准模型'))

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
            "answer_preview": str(result.get('answer', ''))[:200] + "..." if result.get('answer') else "无内容"
        },
        "dify_config": {
            "api_key_configured": bool(DIFY_API_KEY and not DIFY_API_KEY.startswith("app-xxx")),
            "workflow_id": WORKFLOW_ID
        }
    })

# ========== 错误处理 ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "404 Not Found",
        "message": "请求的URL不存在",
        "available_endpoints": [
            "/",
            "/submit (POST)",
            "/results",
            "/api/health",
            "/api/test-workflow"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    print(f"500错误: {str(error)}")
    return jsonify({
        "error": "500 Internal Server Error",
        "message": "服务器内部错误",
        "suggestion": "请稍后重试"
    }), 500

# ========== 启动应用 ==========
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 60)
    print("养老金规划系统启动中...")
    print(f"Dify API配置: {'✅ 已配置' if DIFY_API_KEY and not DIFY_API_KEY.startswith('app-xxx') else '❌ 未配置'}")
    print(f"工作流ID: {'✅ ' + WORKFLOW_ID if WORKFLOW_ID else '❌ 未配置'}")
    print(f"本地访问: http://localhost:{port}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    # Vercel需要这个
    application = app
