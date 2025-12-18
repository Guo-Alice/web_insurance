"""
养老金规划Web应用 - 连接到Dify工作流
用户填写信息 → 调用Dify工作流 → 显示结果
"""
from flask import Flask, render_template, request, jsonify, session
import requests
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pension-planning-secret-key-2024")
app.config['SESSION_TYPE'] = 'filesystem'

# Dify配置
DIFY_API_KEY = os.environ.get("DIFY_API_KEY", "app-rd6ag4AYRsDqurCZ4KokIbNI")  # 在环境变量中设置
WORKFLOW_ID = os.environ.get("WORKFLOW_ID", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
DIFY_API_URL = "https://api.dify.ai/v1"


def call_dify_workflow(user_data):
    """
    调用Dify工作流API
    如果配置了Dify API，则调用真实API；否则返回模拟数据
    """
    # 如果没有配置Dify API Key，使用模拟数据
    if not DIFY_API_KEY or DIFY_API_KEY == "app-xxx":
        return get_mock_ai_response(user_data)
    
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 根据配置选择API端点
    if WORKFLOW_ID:
        # 使用工作流API
        payload = {
            "inputs": user_data,
            "response_mode": "blocking",
            "user": f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        try:
            response = requests.post(
                f"{DIFY_API_URL}/workflows/run",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Dify API错误: {response.status_code} - {response.text}")
                return get_mock_ai_response(user_data)
                
        except Exception as e:
            print(f"调用Dify失败: {str(e)}")
            return get_mock_ai_response(user_data)
    
    else:
        # 使用对话API
        # 构建查询文本
        query = f"""
        用户信息：
        - 年龄：{user_data.get('age', '未知')}岁
        - 年收入：{user_data.get('annual_income', '未知')}万元
        - 风险偏好：{user_data.get('risk_tolerance', '未知')}
        - 所在地区：{user_data.get('location', '未知')}
        - 社保类型：{user_data.get('social_security', '未知')}
        - 退休年龄：{user_data.get('retirement_age', '未知')}岁
        - 投资金额：{user_data.get('investment_amount', '未知')}万元
        
        请提供养老金规划建议，包括：
        1. 适合的产品类型
        2. 风险匹配建议
        3. 具体的投资策略
        """
        
        payload = {
            "inputs": user_data,
            "query": query,
            "response_mode": "blocking",
            "conversation_id": f"pension_{datetime.now().strftime('%Y%m%d')}",
            "user": f"user_{user_data.get('age', 'unknown')}"
        }
        
        try:
            response = requests.post(
                f"{DIFY_API_URL}/chat-messages",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Dify对话API错误: {response.status_code}")
                return get_mock_ai_response(user_data)
                
        except Exception as e:
            print(f"调用Dify对话API失败: {str(e)}")
            return get_mock_ai_response(user_data)

def get_mock_ai_response(user_data):
    """
    生成模拟AI响应（当Dify API不可用时使用）
    """
    age = int(user_data.get('age', 30))
    income = float(user_data.get('annual_income', 20))
    risk = user_data.get('risk_tolerance', '平衡型')
    location = user_data.get('location', '全国')
    investment = float(user_data.get('investment_amount', 10))
    
    # 基于用户数据生成个性化建议
    recommendations = []
    
    # 1. 基本信息总结
    recommendations.append(f"👤 **用户画像分析**")
    recommendations.append(f"年龄：{age}岁 | 年收入：{income}万元 | 风险偏好：{risk}")
    recommendations.append(f"地区：{location} | 计划投资：{investment}万元")
    recommendations.append("")
    
    # 2. 风险评估
    recommendations.append(f"🎯 **风险评估结果**")
    if risk == '保守型':
        recommendations.append("• 风险承受能力：低")
        recommendations.append("• 适合保本型产品")
    elif risk == '稳健型':
        recommendations.append("• 风险承受能力：中低")
        recommendations.append("• 适合稳健增值产品")
    elif risk == '平衡型':
        recommendations.append("• 风险承受能力：中等")
        recommendations.append("• 适合平衡型产品组合")
    elif risk == '成长型':
        recommendations.append("• 风险承受能力：中高")
        recommendations.append("• 适合成长型产品")
    else:  # 进取型
        recommendations.append("• 风险承受能力：高")
        recommendations.append("• 适合进取型产品")
    recommendations.append("")
    
    # 3. 产品推荐
    recommendations.append(f"📊 **养老金产品推荐**")
    
    if age < 35:
        recommendations.append("**青年阶段（<35岁）**")
        recommendations.append("• 推荐指数基金定投（占60%）")
        recommendations.append("• 推荐成长型年金保险（占30%）")
        recommendations.append("• 推荐货币基金（占10%）")
    elif age < 50:
        recommendations.append("**中年阶段（35-50岁）**")
        recommendations.append("• 推荐平衡型基金（占50%）")
        recommendations.append("• 推荐稳健型年金保险（占40%）")
        recommendations.append("• 推荐债券基金（占10%）")
    else:
        recommendations.append("**中老年阶段（>50岁）**")
        recommendations.append("• 推荐稳健型年金保险（占60%）")
        recommendations.append("• 推荐债券基金（占30%）")
        recommendations.append("• 推荐银行存款（占10%）")
    recommendations.append("")
    
    # 4. 投资策略
    recommendations.append(f"💡 **投资策略建议**")
    recommendations.append(f"• 每月定投：建议每月投资收入的{min(20, int(100/age))}%")
    recommendations.append(f"• 投资期限：建议{65-age}年")
    recommendations.append(f"• 预期年化收益：{get_expected_return(risk)}%")
    recommendations.append(f"• 退休时预计积累：约{calculate_retirement_amount(age, income, investment, risk)}万元")
    
    # 转换为AI响应格式
    return {
        "success": True,
        "answer": "\n".join(recommendations),
        "data": {
            "outputs": {
                "pension_report": "\n".join(recommendations),
                "risk_assessment": risk,
                "expected_return": get_expected_return(risk),
                "recommended_products": get_recommended_products(age, risk)
            }
        },
        "source": "模拟AI数据（Dify API未配置或调用失败）"
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

def calculate_retirement_amount(age, income, investment, risk):
    """计算退休时预计积累金额"""
    years_to_retire = 65 - age
    monthly_investment = (income * 10000 * 0.1) / 12  # 假设投资收入的10%
    annual_return = get_expected_return(risk) / 100
    
    # 简化计算：复利公式
    total = investment * 10000 * (1 + annual_return) ** years_to_retire
    total += monthly_investment * 12 * ((1 + annual_return) ** years_to_retire - 1) / annual_return
    
    return round(total / 10000, 1)

def get_recommended_products(age, risk):
    """获取推荐产品列表"""
    if age < 35:
        base_products = ["指数基金", "成长型年金"]
    elif age < 50:
        base_products = ["平衡型基金", "稳健年金"]
    else:
        base_products = ["稳健年金", "债券基金"]
    
    if risk in ['保守型', '稳健型']:
        base_products.append("银行存款")
    elif risk in ['成长型', '进取型']:
        base_products.append("股票基金")
    
    return base_products

# ========== Flask 路由 ==========
@app.route('/')
def index():
    """显示主页"""
    session['session_id'] = str(uuid.uuid4())[:8]
    # 检查Dify配置状态
    dify_configured = bool(DIFY_API_KEY and DIFY_API_KEY != "app-xxx")
    return render_template('index.html', dify_configured=dify_configured)

@app.route('/submit', methods=['POST'])
def submit_form():
    """处理表单提交"""
    try:
        data = request.form.to_dict()
        
        # 验证数据
        if not data.get('age') or not data.get('annual_income'):
            return jsonify({
                "success": False,
                "message": "请填写年龄和年收入"
            })
        
        # 准备用户数据
        user_data = {
            "age": data.get('age'),
            "annual_income": data.get('annual_income'),
            "risk_tolerance": data.get('risk_tolerance', '平衡型'),
            "location": data.get('location', '全国'),
            "social_security": data.get('social_security', '城镇职工'),
            "retirement_age": data.get('retirement_age', '60'),
            "investment_amount": data.get('investment_amount', '10'),
            "insurance_type": data.get('insurance_type', '全部')
        }
        
        # 调用AI分析（Dify或模拟数据）
        ai_result = call_dify_workflow(user_data)
        
        # 保存到session
        session['user_data'] = user_data
        session['ai_result'] = ai_result
        session['analysis_time'] = datetime.now().isoformat()
        
        return jsonify({
            "success": True,
            "message": "分析完成！",
            "redirect": "/results",
            "ai_source": ai_result.get('source', 'Dify AI')
        })
        
    except Exception as e:
        print(f"表单提交错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"系统错误：{str(e)}"
        })

@app.route('/results')
def show_results():
    """显示结果页面"""
    if 'user_data' not in session:
        return "请先提交表单", 400
    
    user_data = session.get('user_data', {})
    ai_result = session.get('ai_result', {})
    
    return render_template('results.html', 
                         user_data=user_data,
                         ai_result=ai_result)

@app.route('/api/test-dify')
def test_dify():
    """测试Dify连接"""
    test_data = {
        "age": 35,
        "annual_income": 25.0,
        "risk_tolerance": "平衡型",
        "location": "北京",
        "social_security": "城镇职工",
        "retirement_age": 60,
        "investment_amount": 12.0
    }
    
    result = call_dify_workflow(test_data)
    
    return jsonify({
        "status": "online",
        "service": "养老金规划系统",
        "timestamp": datetime.now().isoformat(),
        "dify_config": {
            "api_key_set": bool(DIFY_API_KEY and DIFY_API_KEY != "app-xxx"),
            "workflow_id_set": bool(WORKFLOW_ID),
            "api_url": DIFY_API_URL
        },
        "test_result": {
            "ai_source": result.get('source', '未知'),
            "has_data": bool(result),
            "response_keys": list(result.keys()) if isinstance(result, dict) else []
        },
        "endpoints": {
            "home": "/",
            "submit": "/submit (POST)",
            "results": "/results",
            "health": "/api/health",
            "test": "/api/test-dify",
            "debug": "/api/debug"
        }
    })

@app.route('/api/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "养老金规划系统",
        "version": "2.0.0",
        "dify_integration": bool(DIFY_API_KEY and DIFY_API_KEY != "app-xxx")
    })

@app.route('/api/debug')
def debug_info():
    """调试信息"""
    return jsonify({
        "headers": dict(request.headers),
        "args": dict(request.args),
        "session_keys": list(session.keys()) if session else [],
        "dify_config": {
            "api_key_present": bool(DIFY_API_KEY),
            "api_key_prefix": DIFY_API_KEY[:10] if DIFY_API_KEY else "None",
            "workflow_id_present": bool(WORKFLOW_ID)
        }
    })

@app.route('/api/dify-config')
def dify_config():
    """显示Dify配置状态"""
    return jsonify({
        "dify_api_key_configured": bool(DIFY_API_KEY and DIFY_API_KEY != "app-xxx"),
        "dify_workflow_id_configured": bool(WORKFLOW_ID),
        "environment": {
            "FLASK_APP": os.environ.get("FLASK_APP", "未设置"),
            "VERCEL_ENV": os.environ.get("VERCEL_ENV", "未设置"),
            "PYTHON_VERSION": os.environ.get("PYTHON_VERSION", "未设置")
        }
    })

# 错误处理
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
            "/api/test-dify",
            "/api/debug",
            "/api/dify-config"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "500 Internal Server Error",
        "message": "服务器内部错误",
        "suggestion": "请检查应用配置或稍后重试"
    }), 500

# ========== 应用启动 ==========
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 60)
    print("养老金规划系统启动中...")
    print(f"Dify API配置: {'✅ 已配置' if DIFY_API_KEY and DIFY_API_KEY != 'app-xxx' else '❌ 未配置'}")
    print(f"工作流ID: {'✅ 已配置' if WORKFLOW_ID else '❌ 未配置'}")
    print(f"本地访问: http://localhost:{port}")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Vercel需要这个
    application = app
