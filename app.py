"""
养老金规划系统 - 完整修复版
调用Dify API生成报告，使用本地静态资源
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
import requests
from datetime import datetime
import uuid

# 获取当前文件的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 创建Flask应用
app = Flask(__name__,
            static_folder=os.path.join(BASE_DIR, 'static'),
            template_folder=os.path.join(BASE_DIR, 'templates'))
app.secret_key = os.environ.get("SECRET_KEY", "pension-secret-key-2024")

# Dify配置 - 请确保这里的API Key是正确的
DIFY_API_KEY = "app-rd6ag4AYRsDqurCZ4KokIbNI"
DIFY_API_BASE_URL = "https://api.dify.ai/v1"

# 确保目录存在
static_dir = os.path.join(BASE_DIR, 'static')
css_dir = os.path.join(static_dir, 'css')
js_dir = os.path.join(static_dir, 'js')
os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'templates'), exist_ok=True)

def call_dify_api(user_data):
    """调用Dify API生成养老金规划报告"""
    try:
        if not DIFY_API_KEY or DIFY_API_KEY.startswith("app-xxx"):
            raise Exception("API Key未配置或无效")
        
        api_url = f"{DIFY_API_BASE_URL}/chat-messages"
        headers = {
            "Authorization": f"Bearer {DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 构建用户查询
        user_query = f"""
请为以下用户生成详细的养老金规划建议：

用户信息：
- 年龄：{user_data.get('age')}岁
- 年收入：{user_data.get('annual_income')}万元
- 风险偏好：{user_data.get('risk_tolerance')}
- 所在地区：{user_data.get('location')}
- 社保类型：{user_data.get('social_security')}
- 计划退休年龄：{user_data.get('retirement_age')}岁
- 计划投资金额：{user_data.get('investment_amount')}万元

请提供详细的养老金规划建议，包括：
1. 资产配置建议
2. 预期收益分析
3. 每月储蓄建议
4. 风险提示
5. 长期规划策略

请以专业、清晰的方式呈现建议。
"""
        
        payload = {
            "inputs": {
                "年龄": user_data.get('age'),
                "年收入": user_data.get('annual_income'),
                "风险偏好": user_data.get('risk_tolerance'),
                "地区": user_data.get('location'),
                "社保类型": user_data.get('social_security'),
                "计划退休年龄": user_data.get('retirement_age'),
                "计划投资金额": user_data.get('investment_amount')
            },
            "query": user_query,
            "response_mode": "blocking",
            "user": f"user_{uuid.uuid4().hex[:8]}"
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # 提取回答内容
            answer = result.get('answer') or result.get('data', {}).get('answer')
            if answer:
                return {
                    "success": True,
                    "answer": answer,
                    "source": "Dify AI智能分析"
                }
            else:
                raise Exception("API响应中没有找到答案")
        else:
            raise Exception(f"API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"Dify API调用失败: {str(e)}")
        # 如果API调用失败，使用本地备用方案
        return {
            "success": True,
            "answer": generate_fallback_report(user_data),
            "source": "本地智能分析引擎（Dify API暂时不可用）",
            "error": str(e)
        }

def generate_fallback_report(user_data):
    """本地备用报告生成"""
    try:
        age = int(user_data.get('age', 35))
        income = float(user_data.get('annual_income', 25))
        risk = user_data.get('risk_tolerance', '中')
        investment = float(user_data.get('investment_amount', 12))
        retirement_age = int(user_data.get('retirement_age', 60))
        
        risk_mapping = {
            '低': ('保守型', '债券基金(50%) + 年金保险(40%) + 货币基金(10%)', '4-6%'),
            '中低': ('稳健型', '债券基金(40%) + 年金保险(40%) + 平衡基金(20%)', '4-6%'),
            '中': ('平衡型', '指数基金(40%) + 混合基金(30%) + 年金保险(30%)', '6-8%'),
            '中高': ('成长型', '股票基金(40%) + 指数基金(30%) + 年金保险(30%)', '7-9%'),
            '高': ('进取型', '股票基金(50%) + 指数基金(30%) + 年金保险(20%)', '8-10%'),
        }
        
        mapped_risk, allocation, expected_return = risk_mapping.get(risk, risk_mapping['中'])
        years_to_retire = max(1, retirement_age - age)
        monthly_saving = income * 0.15
        
        report = f"""
🏦 智能养老金规划报告（本地生成）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 客户基本信息
• 年龄：{age}岁
• 年收入：{income:.1f}万元
• 风险偏好：{risk}（{mapped_risk}）
• 计划投资金额：{investment:.1f}万元
• 计划退休年龄：{retirement_age}岁
• 距离退休还有：{years_to_retire}年

📊 资产配置建议（根据风险偏好定制）
{allocation}

💰 预期收益与储蓄分析
• 建议每月储蓄：{monthly_saving:.1f}万元（年收入15%）
• 退休前累计储蓄：{monthly_saving * 12 * years_to_retire:.1f}万元
• 预计投资增值：{investment * 0.5:.1f}万元
• 预计年化收益率：{expected_return}

💡 核心规划建议
1. 复利效应：{age}岁开始规划，利用时间优势积累财富
2. 投资节奏：退休前10年逐步降低风险，债券/保险占比提升
3. 产品选择：优先选择费率低、长期稳定的指数基金和年金保险

⚠️ 风险提示
• 以上收益为理论测算，实际收益受市场波动影响
• 建议每3-5年重新评估风险承受能力和资产配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report
    except Exception as e:
        return f"生成报告时出错：{str(e)}"

# ========== Flask路由 ==========
@app.route('/')
def index():
    """显示主页"""
    session.clear()
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """处理favicon请求 - 避免500错误"""
    return '', 204

@app.route('/submit', methods=['POST'])
def submit_form():
    """处理表单提交 - 调用Dify API"""
    try:
        # 1. 获取表单数据
        data = request.form.to_dict()
        print(f"收到表单数据: {data}")
        
        # 2. 基本验证
        if not data.get('age') or not data.get('annual_income'):
            return jsonify({
                "success": False,
                "message": "请填写年龄和年收入"
            })
        
        # 3. 准备用户数据
        user_data = {
            "age": data.get('age'),
            "annual_income": data.get('annual_income'),
            "risk_tolerance": data.get('risk_tolerance', '中'),
            "location": data.get('location', '全国'),
            "social_security": data.get('social_security', '城镇职工'),
            "retirement_age": data.get('retirement_age', '60'),
            "investment_amount": data.get('investment_amount', '12')
        }
        
        # 4. 调用Dify API
        print("正在调用Dify API...")
        ai_result = call_dify_api(user_data)
        print("Dify API调用完成")
        
        # 5. 保存到Session
        session['user_data'] = user_data
        session['ai_result'] = ai_result
        session['analysis_time'] = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        
        # 6. 返回成功响应
        return jsonify({
            "success": True,
            "message": "分析完成！",
            "redirect": "/results"
        })
        
    except Exception as e:
        print(f"表单处理异常: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"系统错误: {str(e)}"
        })

@app.route('/results')
def show_results():
    """显示结果页面"""
    if 'user_data' not in session:
        return redirect('/')
    
    user_data = session.get('user_data', {})
    ai_result = session.get('ai_result', {})
    analysis_time = session.get('analysis_time', '')
    
    report = ai_result.get('answer', '未能生成规划报告。')
    source = ai_result.get('source', '本地分析引擎')
    error = ai_result.get('error', '')
    
    return render_template(
        'results.html',
        user_data=user_data,
        report=report,
        source=source,
        analysis_time=analysis_time,
        error=error
    )

if __name__ == '__main__':
    print("="*80)
    print("养老金规划系统启动")
    print(f"Dify API Key: {'已配置' if DIFY_API_KEY and not DIFY_API_KEY.startswith('app-xxx') else '未配置或无效'}")
    print(f"静态文件目录: {static_dir}")
    print(f"本地访问: http://localhost:5000")
    print("="*80)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
