"""
养老金规划系统 - 最终稳定版（整合Dify API超长超时+代理禁用）
"""
from flask import Flask, render_template, request, jsonify, session
import os
import json
import requests
import traceback
from datetime import datetime
import uuid
import time
import sys

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pension-planning-secret-key-2024")

# Dify配置（固定密钥，超时设为70秒）
DIFY_API_KEY = "app-rd6ag4AYRsDqurCZ4KokIbNI"  # 直接配置有效密钥
DIFY_API_BASE_URL = "https://api.dify.ai/v1"
DIFY_TIMEOUT = 70  # 核心修改：超时设为70秒
DIFY_DISABLE_PROXY = True  # 禁用代理解决ProxyError

# ========== 核心：整合测试代码的稳定Dify API调用逻辑 ==========
def call_dify_chat(user_data, user_query):
    """
    调用Dify对话API - 整合超长超时+代理禁用+详细日志
    """
    print(f"\n{'='*80}")
    print(f"📤 开始调用Dify对话API | 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # 检查密钥有效性
    if not DIFY_API_KEY or DIFY_API_KEY.startswith("app-xxx"):
        print("⚠️ API Key未配置或无效，使用标准模型回退")
        return get_fallback_response(user_data, "API Key配置无效")
    
    # 构建API请求参数
    api_url = f"{DIFY_API_BASE_URL}/chat-messages"
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建自定义变量（对应Dify App的变量）
    custom_inputs = {
        "年龄": user_data.get('age', '30'),
        "年收入": user_data.get('annual_income', '20'),
        "风险偏好": user_data.get('risk_tolerance', '平衡型'),
        "地区": user_data.get('location', '全国'),
        "社保类型": user_data.get('social_security', '城镇职工'),
        "计划退休年龄": user_data.get('retirement_age', '60'),
        "计划投资金额": user_data.get('investment_amount', '10')
    }
    
    # 补全用户查询（确保非空）
    user_query_text = user_query or f"""
请根据我的以下情况提供详细的养老金规划建议：
- 年龄：{user_data.get('age')}岁
- 年收入：{user_data.get('annual_income')}万元
- 风险偏好：{user_data.get('risk_tolerance')}
- 地区：{user_data.get('location')}
- 社保类型：{user_data.get('social_security')}
- 计划退休年龄：{user_data.get('retirement_age')}岁
- 计划投资金额：{user_data.get('investment_amount')}万元
要求：建议需具体、可执行，包含资产配置、产品推荐、收益分析、风险管理。
    """.strip()
    
    # 构建请求体（严格符合Dify API规范）
    payload = {
        "inputs": custom_inputs,
        "query": user_query_text,
        "response_mode": "blocking",
        "user": f"pension_user_{uuid.uuid4().hex[:8]}"  # 唯一用户标识
    }
    
    # 打印调试信息
    print(f"🔧 API配置:")
    print(f"   URL: {api_url}")
    print(f"   超时: {DIFY_TIMEOUT}秒")
    print(f"   禁用代理: {DIFY_DISABLE_PROXY}")
    print(f"📥 自定义变量: {json.dumps(custom_inputs, ensure_ascii=False)}")
    print(f"📝 用户查询: {user_query_text[:100]}...")
    
    # 构建requests参数（核心：禁用代理+超长超时）
    request_kwargs = {
        "headers": headers,
        "json": payload,
        "timeout": DIFY_TIMEOUT,
    }
    # 禁用代理（解决ProxyError）
    if DIFY_DISABLE_PROXY:
        request_kwargs["proxies"] = {}
        # 额外清空环境变量代理（双重保障）
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
    
    try:
        start_time = time.time()
        
        # 发送请求（复用测试代码的稳定逻辑）
        response = requests.post(api_url,** request_kwargs)
        
        elapsed = time.time() - start_time
        print(f"\n📤 Dify响应结果 | 耗时: {elapsed:.2f}秒 | 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Dify API调用成功！响应长度: {len(json.dumps(result))}字符")
                return extract_chat_response(result)
            except json.JSONDecodeError as e:
                error_msg = f"响应JSON解析失败: {str(e)} | 响应内容: {response.text[:500]}"
                print(f"❌ {error_msg}")
                return get_fallback_response(user_data, error_msg)
        else:
            error_detail = response.text[:500] if response.text else "无错误详情"
            error_msg = f"API返回错误状态码: {response.status_code} | 详情: {error_detail}"
            print(f"❌ {error_msg}")
            return get_fallback_response(user_data, error_msg)
            
    except requests.exceptions.Timeout:
        error_msg = f"请求超时（{DIFY_TIMEOUT}秒），网络或Dify服务响应慢"
        print(f"❌ {error_msg}")
        return get_fallback_response(user_data, error_msg)
    except requests.exceptions.ConnectionError as e:
        error_msg = f"网络连接错误: {str(e)} | 请检查网络或代理设置"
        print(f"❌ {error_msg}")
        return get_fallback_response(user_data, error_msg)
    except Exception as e:
        error_msg = f"未知异常: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return get_fallback_response(user_data, error_msg)

def extract_chat_response(result):
    """提取Dify响应内容（兼容多种响应格式）"""
    try:
        print(f"🔍 解析Dify响应 | 响应结构: {list(result.keys())}")
        
        # 优先从标准位置提取
        extract_paths = [
            ('data', 'answer'),
            ('answer',),
            ('data', 'message'),
            ('message',),
            ('data', 'content'),
            ('content',)
        ]
        
        # 遍历所有可能的字段路径
        for path in extract_paths:
            value = result
            for key in path:
                if key not in value:
                    value = None
                    break
                value = value[key]
            
            if value and isinstance(value, str) and value.strip():
                answer = value.strip()
                print(f"✅ 从路径 {'.'.join(path)} 提取到回答（长度: {len(answer)}字符）")
                return {
                    "success": True,
                    "answer": answer,
                    "source": "Dify AI对话模型",
                    "raw_response": result
                }
        
        # 兜底：返回原始响应（用于调试）
        raw_str = json.dumps(result, ensure_ascii=False, indent=2)[:1000]
        print(f"⚠️ 未找到标准回答字段，返回原始响应预览")
        return {
            "success": True,
            "answer": f"【Dify响应格式说明】\n\n原始响应内容:\n{raw_str}\n\n（注：未识别到标准回答字段，可检查Dify App配置）",
            "source": "Dify AI（原始响应）",
            "raw_response": result
        }
        
    except Exception as e:
        error_msg = f"解析响应异常: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return {
            "success": False,
            "answer": f"解析AI回答失败: {error_msg}",
            "source": "系统错误"
        }

def get_fallback_response(user_data, error_reason=""):
    """回退响应：当Dify API不可用时生成标准建议"""
    print(f"🔧 触发回退响应 | 原因: {error_reason}")
    advice = generate_standard_advice(user_data)
    
    response = {
        "success": True,
        "answer": advice,
        "source": "标准养老金规划模型"
    }
    
    if error_reason:
        response["system_note"] = f"注：Dify AI服务暂时不可用（{error_reason}），已使用本地标准模型生成建议"
    
    return response

def generate_standard_advice(user_data):
    """生成标准化养老金规划建议"""
    try:
        # 解析用户数据（容错处理）
        age = int(user_data.get('age', 30)) if user_data.get('age', '30').isdigit() else 30
        income = float(user_data.get('annual_income', 20)) if user_data.get('annual_income', '20').replace('.','').isdigit() else 20
        risk = user_data.get('risk_tolerance', '平衡型')
        investment = float(user_data.get('investment_amount', 10)) if user_data.get('investment_amount', '10').replace('.','').isdigit() else 10
        retirement_age = int(user_data.get('retirement_age', 60)) if user_data.get('retirement_age', '60').isdigit() else 60
        
        # 风险偏好映射
        risk_mapping = {
            '低': ('稳健型', '债券基金(50%) + 年金保险(40%) + 货币基金(10%)', '4-6%'),
            '中低': ('稳健型', '债券基金(40%) + 年金保险(40%) + 平衡基金(20%)', '4-6%'),
            '平衡型': ('平衡型', '指数基金(40%) + 混合基金(30%) + 年金保险(30%)', '6-8%'),
            '中高': ('成长型', '股票基金(40%) + 指数基金(30%) + 年金保险(30%)', '7-9%'),
            '高': ('进取型', '股票基金(50%) + 指数基金(30%) + 年金保险(20%)', '8-10%'),
            '保守型': ('稳健型', '债券基金(50%) + 年金保险(40%) + 货币基金(10%)', '4-6%'),
            '成长型': ('成长型', '股票基金(40%) + 指数基金(30%) + 年金保险(30%)', '7-9%'),
            '进取型': ('进取型', '股票基金(50%) + 指数基金(30%) + 年金保险(20%)', '8-10%'),
        }
        
        mapped_risk, allocation, expected_return = risk_mapping.get(risk, risk_mapping['平衡型'])
        
        # 计算关键指标
        years_to_retire = max(1, retirement_age - age)
        monthly_saving = income * 0.15  # 每月建议储蓄（年收入15%）
        total_saving = monthly_saving * 12 * years_to_retire  # 累计储蓄
        total_asset = total_saving + investment * 1.5  # 预计总资产（含投资增值）
        
        # 生成建议文本
        advice = f"""
🏦 智能养老金规划报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 客户基本信息
• 年龄：{age}岁
• 年收入：{income:.1f}万元
• 风险偏好：{risk}（{mapped_risk}）
• 计划投资金额：{investment:.1f}万元
• 计划退休年龄：{retirement_age}岁
• 距离退休还有：{years_to_retire}年
• 地区/社保类型：{user_data.get('location', '全国')}/{user_data.get('social_security', '城镇职工')}

📊 资产配置建议（根据风险偏好定制）
{allocation}

💰 预期收益与储蓄分析
• 建议每月储蓄：{monthly_saving:.1f}万元（年收入15%）
• 退休前累计储蓄：{total_saving:.1f}万元
• 预计投资增值：{investment * 0.5:.1f}万元
• 退休时预计总资产：{total_asset:.1f}万元
• 预计年化收益率：{expected_return}

💡 核心规划建议
1. 复利效应：{age}岁开始规划，比{age+10}岁开始多获得约{(1 + float(expected_return.strip('%'))/100)** 10 - 1:.1%}的收益
2. 投资节奏：退休前10年（{retirement_age-10}岁）逐步降低风险，债券/保险占比提升至70%以上
3. 产品选择：优先选择费率低、长期稳定的指数基金和年金保险，避免短期投机
4. 风险控制：单一产品投资不超过总资产30%，每年复盘调整一次配置

⚠️ 风险提示
• 以上收益为理论测算，实际收益受市场波动影响
• 养老金规划需结合社保、企业年金等综合考虑
• 建议每3-5年重新评估风险承受能力和资产配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return advice
    except Exception as e:
        error_msg = f"生成标准建议时出错：{str(e)}"
        print(f"❌ {error_msg}")
        return f"""
🏦 智能养老金规划报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 数据解析异常：{error_msg}

💡 通用养老金规划建议
1. 尽早开始储蓄，利用复利效应提升长期收益
2. 分散投资，降低单一资产风险
3. 结合社保和商业保险，构建多层次养老保障
4. 根据年龄和风险偏好动态调整资产配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ========== Flask路由（保留原有所有功能） ==========
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
        print(f"\n📋 收到表单提交 | SessionID: {session.get('session_id', 'unknown')}")
        print(f"表单数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 基本字段验证
        required_fields = ['age', 'annual_income']
        missing_fields = [field for field in required_fields if not (data.get(field) and data.get(field).strip())]
        
        if missing_fields:
            return jsonify({
                "success": False,
                "message": f"请填写完整以下必填字段：{'、'.join(missing_fields)}"
            })
        
        # 整理用户数据（容错处理）
        user_data = {
            "age": data.get('age', '30').strip(),
            "annual_income": data.get('annual_income', '20').strip(),
            "risk_tolerance": data.get('risk_tolerance', '平衡型').strip(),
            "location": data.get('location', '全国').strip(),
            "social_security": data.get('social_security', '城镇职工').strip(),
            "retirement_age": data.get('retirement_age', '60').strip(),
            "investment_amount": data.get('investment_amount', '10').strip()
        }
        
        # 构建用户查询
        user_query = data.get('user_query', '').strip() or f"请根据我的年龄{user_data['age']}岁、年收入{user_data['annual_income']}万元、风险偏好{user_data['risk_tolerance']}等条件，提供详细的、可执行的养老金规划建议，包括资产配置、产品推荐、收益分析和风险管理措施。"
        
        # 调用Dify API（核心：使用稳定版调用函数）
        ai_result = call_dify_chat(user_data, user_query)
        
        # 保存到Session
        session['user_data'] = user_data
        session['ai_result'] = ai_result
        session['analysis_time'] = datetime.now().isoformat()
        
        # 返回响应
        return jsonify({
            "success": True,
            "message": "养老金规划分析完成！",
            "redirect": "/results",
            "ai_source": ai_result.get('source', '标准模型'),
            "system_note": ai_result.get('system_note', '')
        })
        
    except Exception as e:
        error_msg = f"表单处理异常: {str(e)}"
        print(f"🔥 {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "message": "系统繁忙，请稍后重试",
            "error": error_msg
        })

@app.route('/results')
def show_results():
    """显示结果页面"""
    # 检查Session有效性
    if 'user_data' not in session:
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>养老金规划系统 - 错误</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="alert alert-warning shadow-sm">
                    <h4 class="alert-heading">📋 请先提交规划信息</h4>
                    <p>您还未提交任何养老金规划相关信息，请先返回首页填写。</p>
                    <hr>
                    <a href="/" class="btn btn-primary">返回首页填写信息</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    # 从Session获取数据
    user_data = session.get('user_data', {})
    ai_result = session.get('ai_result', {})
    analysis_time = session.get('analysis_time', '')
    
    # 格式化时间
    try:
        dt = datetime.fromisoformat(analysis_time.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y年%m月%d日 %H:%M:%S')
    except:
        formatted_time = analysis_time or "未知时间"
    
    # 提取报告内容
    report = ai_result.get('answer', '未能生成规划报告，请重新提交。').strip()
    source = ai_result.get('source', '标准模型')
    system_note = ai_result.get('system_note', '')
    
    # 渲染结果页面
    return render_template(
        'results.html',
        user_data=user_data,
        report=report,
        source=source,
        system_note=system_note,
        analysis_time=formatted_time
    )

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "养老金规划系统（稳定版）",
        "timestamp": datetime.now().isoformat(),
        "dify_config": {
            "api_key_configured": bool(DIFY_API_KEY and not DIFY_API_KEY.startswith("app-xxx")),
            "api_url": f"{DIFY_API_BASE_URL}/chat-messages",
            "timeout": DIFY_TIMEOUT,
            "disable_proxy": DIFY_DISABLE_PROXY
        },
        "session_id": session.get('session_id', 'none')
    })

@app.route('/api/test-chat-api')
def test_chat_api():
    """测试Dify API连通性"""
    test_user_data = {
        "age": "35",
        "annual_income": "30",
        "risk_tolerance": "平衡型",
        "location": "北京",
        "social_security": "城镇职工",
        "retirement_age": "60",
        "investment_amount": "20"
    }
    test_query = "请提供一份简洁的35岁北京用户的养老金规划建议（不超过500字）"
    
    result = call_dify_chat(test_user_data, test_query)
    
    return jsonify({
        "test_info": {
            "name": "Dify对话API测试",
            "user_data": test_user_data,
            "query": test_query,
            "timeout": DIFY_TIMEOUT,
            "disable_proxy": DIFY_DISABLE_PROXY
        },
        "api_result": result
    })

# ========== 错误处理 ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "404 Not Found",
        "message": "请求的页面不存在",
        "suggestion": "请访问 http://localhost:5000 进入养老金规划系统首页"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    error_msg = f"服务器内部错误: {str(error)}"
    print(f"🔥 500错误: {error_msg}")
    traceback.print_exc()
    
    return jsonify({
        "error": "500 Internal Server Error",
        "message": "服务器处理请求时出错，请稍后重试",
        "debug": error_msg if app.debug else "生产环境已隐藏错误详情"
    }), 500

# ========== 启动应用 ==========
if __name__ == '__main__':
    # 打印启动信息
    print("="*80)
    print("养老金规划系统 - 稳定版启动")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dify API配置:")
    print(f"  - API Key: {DIFY_API_KEY[:8]}****{DIFY_API_KEY[-4:]}")
    print(f"  - API URL: {DIFY_API_BASE_URL}/chat-messages")
    print(f"  - 超时时间: {DIFY_TIMEOUT}秒")
    print(f"  - 禁用代理: {DIFY_DISABLE_PROXY}")
    print(f"本地访问地址: http://localhost:5000")
    print("="*80)
    
    # 启动Flask应用
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,  # 开发环境开启调试
        threaded=True  # 启用多线程处理请求
    )
else:
    # 生产环境WSGI配置
    application = app
