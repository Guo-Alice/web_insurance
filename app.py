"""
养老金规划系统 - 修正静态文件路径版
"""
from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
import os
import json
import requests
import traceback
from datetime import datetime
import uuid
import time

# 创建 Flask 应用，明确指定静态文件夹路径
app = Flask(__name__, 
            static_folder='static', 
            static_url_path='/static')
app.secret_key = os.environ.get("SECRET_KEY", "pension-planning-secret-key-2024")

# Dify配置
DIFY_API_KEY = "app-rd6ag4AYRsDqurCZ4KokIbNI"
DIFY_API_BASE_URL = "https://api.dify.ai/v1"
DIFY_TIMEOUT = 70
DIFY_DISABLE_PROXY = True

# 确保static目录存在
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/fonts', exist_ok=True)
os.makedirs('templates', exist_ok=True)

def call_dify_chat(user_data, user_query):
    """调用Dify对话API"""
    try:
        if not DIFY_API_KEY or DIFY_API_KEY.startswith("app-xxx"):
            return get_fallback_response(user_data, "API Key配置无效")
        
        api_url = f"{DIFY_API_BASE_URL}/chat-messages"
        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        custom_inputs = {
            "年龄": user_data.get('age', '30'),
            "年收入": user_data.get('annual_income', '20'),
            "风险偏好": user_data.get('risk_tolerance', '平衡型'),
            "地区": user_data.get('location', '全国'),
            "社保类型": user_data.get('social_security', '城镇职工'),
            "计划退休年龄": user_data.get('retirement_age', '60'),
            "计划投资金额": user_data.get('investment_amount', '10')
        }
        
        user_query_text = user_query or f"""
请根据我的以下情况提供养老金规划建议：
- 年龄：{user_data.get('age')}岁
- 年收入：{user_data.get('annual_income')}万元
- 风险偏好：{user_data.get('risk_tolerance')}
- 地区：{user_data.get('location')}
- 社保类型：{user_data.get('social_security')}
- 计划退休年龄：{user_data.get('retirement_age')}岁
- 计划投资金额：{user_data.get('investment_amount')}万元
"""
        
        payload = {
            "inputs": custom_inputs,
            "query": user_query_text,
            "response_mode": "blocking",
            "user": f"pension_user_{uuid.uuid4().hex[:8]}"
        }
        
        # 禁用代理
        proxies = {}
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
        response = requests.post(
            api_url, 
            headers=headers, 
            json=payload, 
            timeout=DIFY_TIMEOUT,
            proxies=proxies
        )
        
        if response.status_code == 200:
            result = response.json()
            return extract_chat_response(result)
        else:
            error_msg = f"API错误: {response.status_code}"
            return get_fallback_response(user_data, error_msg)
            
    except Exception as e:
        error_msg = f"请求异常: {str(e)}"
        return get_fallback_response(user_data, error_msg)

def extract_chat_response(result):
    """提取Dify响应内容"""
    try:
        # 尝试从不同路径提取回答
        paths_to_try = [
            result.get('data', {}).get('answer'),
            result.get('answer'),
            result.get('data', {}).get('message'),
            result.get('message'),
            result.get('data', {}).get('content'),
            result.get('content')
        ]
        
        for answer in paths_to_try:
            if answer and isinstance(answer, str) and answer.strip():
                return {
                    "success": True,
                    "answer": answer.strip(),
                    "source": "Dify AI对话模型",
                    "raw_response": result
                }
        
        # 如果没有找到，返回原始响应
        return {
            "success": True,
            "answer": f"【AI响应】\n{json.dumps(result, ensure_ascii=False, indent=2)}",
            "source": "Dify AI",
            "raw_response": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "answer": f"解析AI回答失败: {str(e)}",
            "source": "系统错误"
        }

def get_fallback_response(user_data, error_reason=""):
    """回退响应"""
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
        age = int(user_data.get('age', 30))
        income = float(user_data.get('annual_income', 20))
        risk = user_data.get('risk_tolerance', '平衡型')
        investment = float(user_data.get('investment_amount', 10))
        retirement_age = int(user_data.get('retirement_age', 60))
        
        risk_mapping = {
            '低': ('稳健型', '债券基金(50%) + 年金保险(40%) + 货币基金(10%)', '4-6%'),
            '中低': ('稳健型', '债券基金(40%) + 年金保险(40%) + 平衡基金(20%)', '4-6%'),
            '中': ('平衡型', '指数基金(40%) + 混合基金(30%) + 年金保险(30%)', '6-8%'),
            '中高': ('成长型', '股票基金(40%) + 指数基金(30%) + 年金保险(30%)', '7-9%'),
            '高': ('进取型', '股票基金(50%) + 指数基金(30%) + 年金保险(20%)', '8-10%'),
        }
        
        mapped_risk, allocation, expected_return = risk_mapping.get(risk, risk_mapping['中'])
        
        years_to_retire = max(1, retirement_age - age)
        monthly_saving = income * 0.15
        total_saving = monthly_saving * 12 * years_to_retire
        total_asset = total_saving + investment * 1.5
        
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
1. 复利效应：{age}岁开始规划，利用时间优势积累财富
2. 投资节奏：退休前10年逐步降低风险，债券/保险占比提升
3. 产品选择：优先选择费率低、长期稳定的指数基金和年金保险
4. 风险控制：单一产品投资不超过总资产30%，每年复盘调整

⚠️ 风险提示
• 以上收益为理论测算，实际收益受市场波动影响
• 建议每3-5年重新评估风险承受能力和资产配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return advice
    except Exception as e:
        return f"生成标准建议时出错：{str(e)}"

# ========== Flask路由 ==========
@app.route('/')
def index():
    """显示主页"""
    session.clear()
    session['session_id'] = str(uuid.uuid4())[:8]
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory('static', filename)

@app.route('/submit', methods=['POST'])
def submit_form():
    """处理表单提交"""
    try:
        data = request.form.to_dict()
        print(f"收到表单数据: {data}")
        
        # 基本验证
        if not data.get('age') or not data.get('annual_income'):
            return jsonify({
                "success": False,
                "message": "请填写年龄和年收入"
            })
        
        user_data = {
            "age": data.get('age', '30'),
            "annual_income": data.get('annual_income', '20'),
            "risk_tolerance": data.get('risk_tolerance', '中'),
            "location": data.get('location', '全国'),
            "social_security": data.get('social_security', '城镇职工'),
            "retirement_age": data.get('retirement_age', '60'),
            "investment_amount": data.get('investment_amount', '10')
        }
        
        # 调用Dify API
        user_query = f"为{user_data['age']}岁用户提供养老金规划建议"
        ai_result = call_dify_chat(user_data, user_query)
        
        # 保存到Session
        session['user_data'] = user_data
        session['ai_result'] = ai_result
        session['analysis_time'] = datetime.now().isoformat()
        
        return jsonify({
            "success": True,
            "message": "分析完成！",
            "redirect": "/results"
        })
        
    except Exception as e:
        error_msg = f"表单处理异常: {str(e)}"
        print(f"错误: {error_msg}")
        return jsonify({
            "success": False,
            "message": "系统繁忙，请稍后重试"
        })

@app.route('/results')
def show_results():
    """显示结果页面"""
    if 'user_data' not in session:
        # 重定向到首页
        return redirect(url_for('index'))
    
    user_data = session.get('user_data', {})
    ai_result = session.get('ai_result', {})
    analysis_time = session.get('analysis_time', '')
    
    try:
        dt = datetime.fromisoformat(analysis_time.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y年%m月%d日 %H:%M:%S')
    except:
        formatted_time = analysis_time
    
    report = ai_result.get('answer', '未能生成规划报告。')
    source = ai_result.get('source', '标准模型')
    system_note = ai_result.get('system_note', '')
    
    return render_template(
        'results.html',
        user_data=user_data,
        report=report,
        source=source,
        system_note=system_note,
        analysis_time=formatted_time,
        now=datetime.now()
    )

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "养老金规划系统",
        "timestamp": datetime.now().isoformat()
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         message="页面不存在",
                         title="404错误"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         message="服务器内部错误",
                         title="500错误"), 500

if __name__ == '__main__':
    print("="*80)
    print("养老金规划系统启动")
    print(f"静态文件目录: {app.static_folder}")
    print(f"静态URL路径: {app.static_url_path}")
    print(f"本地访问: http://localhost:5000")
    print("="*80)
    
    # 检查静态文件是否存在
    static_files = [
        'static/css/bootstrap.min.css',
        'static/css/bootstrap-icons.css',
        'static/js/bootstrap.bundle.min.js',
        'static/fonts/bootstrap-icons.woff2',
        'static/fonts/bootstrap-icons.woff'
    ]
    
    for file in static_files:
        if os.path.exists(file):
            print(f"✅ 找到: {file}")
        else:
            print(f"❌ 缺失: {file}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
