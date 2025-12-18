"""
养老金规划系统 - 修复同时支持文本和文件输入
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
DIFY_API_BASE_URL = "https://api.dify.ai/v1"

# ========== 修复输入格式 - 同时支持文本和文件 ==========
def call_dify_workflow(user_data):
    """
    调用Dify工作流API - 同时发送文本和文件输入
    """
    print(f"📤 调用Dify工作流 {WORKFLOW_ID}")
    
    # 检查配置
    if not DIFY_API_KEY or DIFY_API_KEY.startswith("app-xxx"):
        print("⚠️ API Key未配置，使用标准模型")
        return get_fallback_response(user_data, "API Key未配置")
    
    if not WORKFLOW_ID:
        print("⚠️ Workflow ID未配置，使用标准模型")
        return get_fallback_response(user_data, "Workflow ID未配置")
    
    # 关键修复：正确的Authorization格式 - 包含大括号！
    headers = {
        "Authorization": f"Bearer {{{DIFY_API_KEY}}}",
        "Content-Type": "application/json"
    }
    
    # 正确的API端点
    api_url = f"{DIFY_API_BASE_URL}/workflows/{WORKFLOW_ID}/run"
    print(f"✅ 正确API URL: {api_url}")
    
    # 准备用户数据 - 纯文本格式
    input_text = f"年龄:{user_data.get('age')}岁，年收入:{user_data.get('annual_income')}万元，风险偏好:{user_data.get('risk_tolerance')}，地区:{user_data.get('location', '全国')}，社保类型:{user_data.get('social_security', '城镇职工')}，计划退休年龄:{user_data.get('retirement_age', 60)}岁，计划投资金额:{user_data.get('investment_amount', 10)}万元。请提供养老金规划建议。"
    
    # 尝试三种可能的输入格式：
    
    # 格式1: 同时包含text和files（files为空数组）
    print("🔄 尝试格式1: 文本+空文件数组...")
    payload_format1 = {
        "inputs": {
            "input": input_text,  # 文本输入
            "files": []           # 空文件数组
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    result = try_dify_request(api_url, headers, payload_format1, "格式1")
    if result and result.get('success'):
        return result
    
    # 格式2: 只有文本输入（不带files字段）
    print("🔄 尝试格式2: 只有文本输入...")
    payload_format2 = {
        "inputs": {
            "input": input_text  # 只有文本输入
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    result = try_dify_request(api_url, headers, payload_format2, "格式2")
    if result and result.get('success'):
        return result
    
    # 格式3: 使用文件格式（如果需要文件）
    print("🔄 尝试格式3: 文件格式...")
    payload_format3 = {
        "inputs": {
            "input": [  # 文件格式（数组）
                {
                    "transfer_method": "local_file",
                    "upload_file_id": "",
                    "type": "text/plain"
                }
            ]
        },
        "response_mode": "blocking",
        "user": f"user_{user_data.get('age', 'unknown')}"
    }
    
    result = try_dify_request(api_url, headers, payload_format3, "格式3")
    if result and result.get('success'):
        return result
    
    # 如果都失败，使用备选方案
    return get_fallback_response(user_data, "所有格式尝试都失败")

def try_dify_request(api_url, headers, payload, format_name):
    """尝试发送请求到Dify"""
    print(f"📤 尝试{format_name}...")
    print(f"  Payload: {json.dumps(payload, ensure_ascii=False)[:300]}...")
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=20
        )
        
        print(f"📥 {format_name}响应状态: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ {format_name}调用成功！")
                print(f"   响应结构: {list(result.keys())}")
                return extract_dify_response(result)
            except json.JSONDecodeError:
                print(f"❌ {format_name}返回了非JSON响应")
                return None
        else:
            error_msg = response.text[:500] if response.text else "无详情"
            print(f"❌ {format_name}失败: {response.status_code} - {error_msg}")
            return None
            
    except Exception as e:
        print(f"❌ {format_name}请求异常: {str(e)}")
        return None

def extract_dify_response(result):
    """提取Dify响应内容"""
    try:
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
        
        # 从常见位置提取响应
        # 1. 检查 data.outputs
        if 'data' in result and 'outputs' in result['data']:
            outputs = result['data']['outputs']
            for key, value in outputs.items():
                if value and str(value).strip():
                    return {
                        "success": True,
                        "answer": str(value).strip(),
                        "source": "Dify AI工作流",
                        "raw_response": result
                    }
        
        # 2. 检查 data.answer
        if 'data' in result and 'answer' in result['data']:
            return {
                "success": True,
                "answer": str(result['data']['answer']).strip(),
                "source": "Dify AI工作流",
                "raw_response": result
            }
        
        # 3. 检查根级别的字段
        for key in ['answer', 'response', 'text', 'content', 'result']:
            if key in result and result[key]:
                return {
                    "success": True,
                    "answer": str(result[key]).strip(),
                    "source": "Dify AI工作流",
                    "raw_response": result
                }
        
        # 如果都没找到，返回整个响应用于调试
        return {
            "success": True,
            "answer": f"Dify返回了数据但格式未知。原始数据:\n\n{json.dumps(result, ensure_ascii=False, indent=2)}",
            "source": "Dify工作流（原始响应）",
            "raw_response": result
        }
        
    except Exception as e:
        print(f"解析响应异常: {str(e)}")
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

# ========== 添加测试端点 ==========
@app.route('/api/test-input-formats')
def test_input_formats():
    """测试不同的输入格式"""
    headers = {
        "Authorization": f"Bearer {{{DIFY_API_KEY}}}",
        "Content-Type": "application/json"
    }
    
    api_url = f"{DIFY_API_BASE_URL}/workflows/{WORKFLOW_ID}/run"
    
    test_cases = [
        {
            "name": "格式1: 文本+空文件数组",
            "payload": {
                "inputs": {
                    "input": "测试养老金规划",
                    "files": []
                },
                "response_mode": "blocking",
                "user": "user_test"
            }
        },
        {
            "name": "格式2: 只有文本输入",
            "payload": {
                "inputs": {
                    "input": "测试养老金规划"
                },
                "response_mode": "blocking",
                "user": "user_test"
            }
        },
        {
            "name": "格式3: 只有空文件数组",
            "payload": {
                "inputs": {
                    "input": [],  # 空数组
                    "files": []
                },
                "response_mode": "blocking",
                "user": "user_test"
            }
        },
        {
            "name": "格式4: 文件格式（无文件ID）",
            "payload": {
                "inputs": {
                    "input": [
                        {
                            "transfer_method": "local_file",
                            "upload_file_id": "",
                            "type": "text/plain"
                        }
                    ]
                },
                "response_mode": "blocking",
                "user": "user_test"
            }
        },
        {
            "name": "格式5: 混合格式",
            "payload": {
                "inputs": {
                    "text_input": "测试养老金规划",  # 可能的另一个输入名
                    "file_input": []
                },
                "response_mode": "blocking",
                "user": "user_test"
            }
        }
    ]
    
    results = []
    
    for test in test_cases:
        try:
            print(f"\n🔍 测试: {test['name']}")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=test['payload'],
                timeout=15
            )
            
            result = {
                "test_name": test['name'],
                "status_code": response.status_code,
                "request_payload": test['payload']
            }
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    result["response"] = response_json
                    result["success"] = True
                    
                    # 提取输出
                    if 'data' in response_json and 'outputs' in response_json['data']:
                        outputs = response_json['data']['outputs']
                        result["outputs_keys"] = list(outputs.keys())
                        
                        for key, value in outputs.items():
                            if value:
                                result["output_preview"] = str(value)[:200]
                                break
                except:
                    result["response_text"] = response.text[:500]
            else:
                result["error"] = response.text[:500]
                result["success"] = False
                
        except Exception as e:
            result = {
                "test_name": test['name'],
                "error": str(e),
                "success": False
            }
        
        results.append(result)
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "workflow_id": WORKFLOW_ID,
        "api_url": api_url,
        "authorization_header": headers['Authorization'],
        "test_results": results,
        "note": "测试不同的输入格式，找出正确的工作流输入结构"
    })

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
        "workflow_configured": bool(WORKFLOW_ID),
        "api_url": f"{DIFY_API_BASE_URL}/workflows/{WORKFLOW_ID}/run",
        "auth_format": f"Bearer {{{DIFY_API_KEY[:10]}...}}",
        "note": "尝试多种输入格式，包括文本+空文件数组"
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
    print(f"正确的API URL: {DIFY_API_BASE_URL}/workflows/{WORKFLOW_ID}/run")
    print(f"正确的认证头: Bearer {{{DIFY_API_KEY}}}")
    print(f"本地访问: http://localhost:{port}")
    print("测试接口: http://localhost:{port}/api/test-input-formats")
    print("=" * 60)
    print("⚠️ 重要提示: 现在尝试多种输入格式")
    print("   1. 文本+空文件数组")
    print("   2. 只有文本输入")
    print("   3. 文件格式")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    application = app
