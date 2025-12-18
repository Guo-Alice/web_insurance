"""
养老金规划系统 - 修复为正确的对话API调用格式
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
DIFY_API_BASE_URL = "https://api.dify.ai/v1"

# ========== 修复：使用对话API而不是工作流API ==========
def call_dify_chat(user_data, user_query):
    """
    调用Dify对话API（与你的成功示例一致）
    """
    print(f"📤 调用Dify对话API...")
    
    # 检查配置
    if not DIFY_API_KEY or DIFY_API_KEY.startswith("app-xxx"):
        print("⚠️ API Key未配置，使用标准模型")
        return get_fallback_response(user_data, "API Key未配置")
    
    # 正确的API端点 - 对话API！
    api_url = f"{DIFY_API_BASE_URL}/chat-messages"
    print(f"✅ 使用对话API URL: {api_url}")
    
    # 关键修复：正确的Authorization格式（无大括号！）
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建自定义变量（对应App里定义的变量）
    custom_inputs = {
        "年龄": user_data.get('age', '30'),
        "年收入": user_data.get('annual_income', '20'),
        "风险偏好": user_data.get('risk_tolerance', '平衡型'),
        "地区": user_data.get('location', '全国'),
        "社保类型": user_data.get('social_security', '城镇职工'),
        "计划退休年龄": user_data.get('retirement_age', '60'),
        "计划投资金额": user_data.get('investment_amount', '10')
    }
    
    # 用户查询问题
    user_query_text = user_query or f"请根据我的年龄{user_data.get('age')}岁、年收入{user_data.get('annual_income')}万元、风险偏好{user_data.get('risk_tolerance')}等条件，提供详细的养老金规划建议。"
    
    # 构建请求数据（与你的成功示例完全一致）
    payload = {
        "inputs": custom_inputs,  # 自定义变量字典
        "query": user_query_text,  # 用户的核心问题（必填）
        "response_mode": "blocking",  # 阻塞模式
        "user": f"user_{user_data.get('age', 'unknown')}_{uuid.uuid4().hex[:6]}"  # 唯一用户标识
    }
    
    print(f"📤 发送请求到Dify对话API...")
    print(f"  API URL: {api_url}")
    print(f"  自定义变量: {custom_inputs}")
    print(f"  用户查询: {user_query_text}")
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📥 Dify响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Dify对话API调用成功！")
                return extract_chat_response(result)
            except json.JSONDecodeError as e:
                print(f"❌ 响应不是有效的JSON: {str(e)}")
                print(f"   响应内容: {response.text[:500]}")
                return get_fallback_response(user_data, f"Dify返回了非JSON响应: {response.text[:200]}")
        else:
            error_detail = response.text[:500] if response.text else "无详情"
            print(f"❌ Dify API调用失败: {response.status_code}")
            print(f"   错误详情: {error_detail}")
            return get_fallback_response(user_data, f"Dify API返回{response.status_code}错误")
            
    except requests.exceptions.Timeout:
        print("❌ Dify API请求超时")
        return get_fallback_response(user_data, "请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接Dify API失败")
        return get_fallback_response(user_data, "连接失败")
    except Exception as e:
        print(f"❌ 请求Dify API时发生异常: {str(e)}")
        traceback.print_exc()
        return get_fallback_response(user_data, f"请求异常: {str(e)}")

def extract_chat_response(result):
    """提取对话API响应内容"""
    try:
        print(f"📋 解析Dify响应，响应结构: {list(result.keys())}")
        
        # 调试：打印完整响应结构
        if 'data' in result:
            print(f"   data结构: {list(result['data'].keys())}")
        
        # 从对话API的标准响应位置提取
        # 1. 检查 data.answer
        if 'data' in result and 'answer' in result['data']:
            answer = result['data']['answer']
            if answer and str(answer).strip():
                return {
                    "success": True,
                    "answer": str(answer).strip(),
                    "source": "Dify AI对话模型",
                    "raw_response": result
                }
        
        # 2. 检查 data.message
        if 'data' in result and 'message' in result['data']:
            message = result['data']['message']
            if message and str(message).strip():
                return {
                    "success": True,
                    "answer": str(message).strip(),
                    "source": "Dify AI对话模型",
                    "raw_response": result
                }
        
        # 3. 检查根级别的字段
        for key in ['answer', 'response', 'text', 'content', 'result', 'message']:
            if key in result and result[key]:
                content = str(result[key]).strip()
                if content:
                    return {
                        "success": True,
                        "answer": content,
                        "source": "Dify AI对话模型",
                        "raw_response": result
                    }
        
        # 如果都没找到，尝试从data的文本字段查找
        if 'data' in result:
            for key, value in result['data'].items():
                if value and isinstance(value, (str, int, float)) and str(value).strip():
                    return {
                        "success": True,
                        "answer": str(value).strip(),
                        "source": "Dify AI对话模型",
                        "raw_response": result
                    }
        
        # 如果以上都没找到，返回整个响应用于调试
        return {
            "success": True,
            "answer": f"Dify返回了数据但格式不标准。原始数据:\n\n{json.dumps(result, ensure_ascii=False, indent=2)[:1000]}",
            "source": "Dify AI（原始响应）",
            "raw_response": result
        }
        
    except Exception as e:
        print(f"❌ 解析响应异常: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "answer": f"解析响应失败: {str(e)}",
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
        
        # 风险偏好映射
        if risk in ['低', '中低']:
            mapped_risk = '稳健型'
            allocation = "债券基金(40%) + 年金保险(40%) + 平衡基金(20%)"
            expected_return = "4-6%"
        elif risk in ['中', '平衡型']:
            mapped_risk = '平衡型'
            allocation = "指数基金(40%) + 混合基金(30%) + 年金保险(30%)"
            expected_return = "6-8%"
        elif risk in ['中高', '高', '成长型', '进取型']:
            mapped_risk = '成长型'
            allocation = "股票基金(50%) + 指数基金(30%) + 年金保险(20%)"
            expected_return = "8-10%"
        else:
            mapped_risk = '平衡型'
            allocation = "指数基金(40%) + 混合基金(30%) + 年金保险(30%)"
            expected_return = "6-8%"
        
        # 计算退休积蓄
        retirement_age = int(user_data.get('retirement_age', 60))
        years_to_retire = max(1, retirement_age - age)
        monthly_saving = income * 0.15
        
        advice = f"""
🏦 智能养老金规划报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 客户基本信息
• 年龄：{age}岁
• 年收入：{income}万元
• 风险偏好：{risk} ({mapped_risk})
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

# ========== 主要路由 ==========
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
        
        # 用户查询问题（必填）
        user_query = data.get('user_query', '') or f"请根据我的年龄{user_data['age']}岁、年收入{user_data['annual_income']}万元、风险偏好{user_data['risk_tolerance']}等条件，提供详细的养老金规划建议。"
        
        # 调用Dify对话API（使用正确的格式）
        ai_result = call_dify_chat(user_data, user_query)
        
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

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "养老金规划系统",
        "timestamp": datetime.now().isoformat(),
        "dify_configured": bool(DIFY_API_KEY and not DIFY_API_KEY.startswith("app-xxx")),
        "api_url": f"{DIFY_API_BASE_URL}/chat-messages",
        "note": "使用对话API（/v1/chat-messages）"
    })

@app.route('/api/test-chat-api')
def test_chat_api():
    """测试对话API（与成功示例一致）"""
    # 模拟你的成功示例的调用
    test_user_data = {
        "age": "35",
        "annual_income": "30",
        "risk_tolerance": "平衡型",
        "location": "北京",
        "social_security": "城镇职工",
        "retirement_age": "60",
        "investment_amount": "20"
    }
    
    test_query = "请根据我的条件提供养老金规划建议"
    
    result = call_dify_chat(test_user_data, test_query)
    
    return jsonify({
        "test": "对话API测试",
        "user_data": test_user_data,
        "query": test_query,
        "result": result
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
    print(f"使用对话API: {DIFY_API_BASE_URL}/chat-messages")
    print(f"本地访问: http://localhost:{port}")
    print("测试接口: http://localhost:{port}/api/test-chat-api")
    print("=" * 60)
    print("⚠️ 重要提示: 使用对话API格式（与成功示例一致）")
    print("   请求体结构:")
    print("   {")
    print('     "inputs": {自定义变量字典},')
    print('     "query": "用户问题",')
    print('     "response_mode": "blocking",')
    print('     "user": "user_id"')
    print("   }")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    application = app
