"""
养老金规划系统 - 修复模板变量错误版本
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
    调用Dify工作流API
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
    
    # 构建JSON格式的输入数据
    # 根据你的Dify工作流配置，输入变量名为"input"
    input_data = {
        "age": user_data.get('age', '30'),
        "annual_income": user_data.get('annual_income', '20'),
        "risk_tolerance": user_data.get('risk_tolerance', '平衡型'),
        "location": user_data.get('location', '全国'),
        "social_security": user_data.get('social_security', '城镇职工'),
        "retirement_age": user_data.get('retirement_age', '60'),
        "investment_amount": user_data.get('investment_amount', '10')
    }
    
    # 将JSON对象转换为字符串作为input值
    input_string = json.dumps(input_data, ensure_ascii=False)
    
    payload = {
        "inputs": {
            "input": input_string  # 变量名为"input"
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    print(f"发送到Dify的数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
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
            print(f"Dify响应前500字符: {json.dumps(result, ensure_ascii=False)[:500]}...")
            return extract_dify_response(result)
            
        elif response.status_code == 400:
            error_detail = response.text[:500] if response.text else "无详情"
            print(f"❌ Dify 400错误详情: {error_detail}")
            # 尝试另一种格式
            return call_dify_workflow_alternative(user_data, error_detail)
            
        else:
            error_detail = response.text[:200] if response.text else "无详情"
            print(f"❌ Dify API错误 {response.status_code}: {error_detail}")
            return get_fallback_response(user_data, f"Dify API错误 {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Dify API超时")
        return get_fallback_response(user_data, "API超时")
    except Exception as e:
        print(f"❌ 调用Dify异常: {str(e)}")
        traceback.print_exc()
        return get_fallback_response(user_data, f"异常: {str(e)}")


def call_dify_workflow_alternative(user_data, previous_error):
    """尝试另一种输入格式"""
    print("🔄 尝试备选输入格式...")
    
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 备选方案1: 使用纯文本格式
    input_string = f"年龄:{user_data.get('age')}岁,收入:{user_data.get('annual_income')}万元,风险:{user_data.get('risk_tolerance')},地区:{user_data.get('location')},社保:{user_data.get('social_security')},退休年龄:{user_data.get('retirement_age')}岁,投资:{user_data.get('investment_amount')}万元"
    
    # 备选方案2: 使用结构化JSON作为input的值（而不是字符串）
    # input_data = {
    #     "年龄": user_data.get('age'),
    #     "年收入": user_data.get('annual_income'),
    #     "风险偏好": user_data.get('risk_tolerance'),
    #     "地区": user_data.get('location'),
    #     "社保类型": user_data.get('social_security'),
    #     "退休年龄": user_data.get('retirement_age'),
    #     "投资金额": user_data.get('investment_amount')
    # }
    # input_string = json.dumps(input_data, ensure_ascii=False)
    
    payload = {
        "inputs": {
            "input": input_string
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    print(f"备选方案发送到Dify的数据: {json.dumps(payload, ensure_ascii=False)[:300]}...")
    
    try:
        response = requests.post(
            f"{DIFY_API_URL}/workflows/run",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify工作流调用成功（备选方案）")
            return extract_dify_response(result)
        else:
            return get_fallback_response(user_data, f"Dify API错误 {response.status_code}（备选方案）")
            
    except Exception as e:
        return get_fallback_response(user_data, f"备选方案异常: {str(e)}")

def extract_dify_response(result):
    """提取Dify响应内容"""
    try:
        if 'data' in result and 'outputs' in result['data']:
            outputs = result['data']['outputs']
            
            possible_keys = ['answer', 'output', 'response', 'text', 'content', 'result']
            for key in possible_keys:
                if key in outputs and outputs[key]:
                    return {
                        "success": True,
                        "answer": str(outputs[key]),
                        "source": "Dify AI工作流"
                    }
        
        return {
            "success": True,
            "answer": json.dumps(result, ensure_ascii=False, indent=2),
            "source": "Dify工作流（原始响应）"
        }
    except Exception as e:
        return {
            "success": False,
            "answer": f"解析Dify响应失败: {str(e)}",
            "source": "系统错误"
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
        
        return jsonify({
            "success": True,
            "message": "分析完成！",
            "redirect": "/results",
            "ai_source": ai_result.get('source', '系统'),
            "system_note": ai_result.get('system_note', '')
        })
        
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
    
    # 提取报告内容
    report = ai_result.get('answer', '未获取到分析结果')
    if not report or report.strip() == '':
        report = "系统未能生成分析结果，请重新提交或联系客服。"
    
    return render_template('results.html', 
                         user_data=user_data,
                         report=report,
                         source=ai_result.get('source', '标准模型'),
                         system_note=ai_result.get('system_note', ''),
                         analysis_time=analysis_time)

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



