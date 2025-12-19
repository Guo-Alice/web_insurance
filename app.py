"""
养老金规划系统 - 简化修复版
完全本地资源，无图标，无报错
"""
from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
import json
from datetime import datetime
import uuid

# 获取当前文件的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 创建Flask应用
app = Flask(__name__,
            static_folder=os.path.join(BASE_DIR, 'static'),
            static_url_path='/static',
            template_folder=os.path.join(BASE_DIR, 'templates'))
app.secret_key = os.environ.get("SECRET_KEY", "pension-planning-secret-key-2024")

# 确保目录存在
static_dir = os.path.join(BASE_DIR, 'static')
css_dir = os.path.join(static_dir, 'css')
js_dir = os.path.join(static_dir, 'js')
templates_dir = os.path.join(BASE_DIR, 'templates')

os.makedirs(css_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# ========== Flask路由 ==========
@app.route('/')
def index():
    """显示主页"""
    session.clear()
    session['session_id'] = str(uuid.uuid4())[:8]
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """处理favicon请求 - 直接返回空响应避免500错误"""
    try:
        # 如果存在favicon.ico就返回，不存在就返回204
        favicon_path = os.path.join(static_dir, 'favicon.ico')
        if os.path.exists(favicon_path):
            return send_from_directory(static_dir, 'favicon.ico')
        else:
            # 返回204 No Content，浏览器不会报错
            return '', 204
    except Exception:
        # 任何错误都返回204
        return '', 204

@app.route('/submit', methods=['POST'])
def submit_form():
    """处理表单提交 - 简化版，确保不会崩溃"""
    try:
        # 1. 获取表单数据
        data = request.form.to_dict()
        print(f"收到表单数据: {data}")
        
        # 2. 基本验证
        required_fields = ['age', 'annual_income', 'risk_tolerance']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"请填写{field}字段"
                })
        
        # 3. 准备用户数据
        user_data = {
            "age": data.get('age', '30'),
            "annual_income": data.get('annual_income', '20'),
            "risk_tolerance": data.get('risk_tolerance', '中'),
            "location": data.get('location', '全国'),
            "social_security": data.get('social_security', '城镇职工'),
            "retirement_age": data.get('retirement_age', '60'),
            "investment_amount": data.get('investment_amount', '10')
        }
        
        # 4. 生成分析报告（本地生成，不调用外部API）
        report = generate_local_report(user_data)
        
        # 5. 保存到Session
        session['user_data'] = user_data
        session['report'] = report
        session['analysis_time'] = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        
        # 6. 返回成功响应
        return jsonify({
            "success": True,
            "message": "分析完成！",
            "redirect": "/results"
        })
        
    except Exception as e:
        print(f"表单处理异常: {str(e)}")
        # 返回简单错误信息，确保不会崩溃
        return jsonify({
            "success": False,
            "message": "系统繁忙，请稍后重试"
        })

@app.route('/results')
def show_results():
    """显示结果页面"""
    if 'user_data' not in session:
        # 重定向到首页
        return redirect('/')
    
    user_data = session.get('user_data', {})
    report = session.get('report', '未能生成规划报告。')
    analysis_time = session.get('analysis_time', '')
    
    return render_template(
        'results.html',
        user_data=user_data,
        report=report,
        source="本地智能分析引擎",
        analysis_time=analysis_time
    )

def generate_local_report(user_data):
    """本地生成养老金规划报告"""
    try:
        age = int(user_data.get('age', 30))
        income = float(user_data.get('annual_income', 20))
        risk = user_data.get('risk_tolerance', '平衡型')
        investment = float(user_data.get('investment_amount', 10))
        retirement_age = int(user_data.get('retirement_age', 60))
        location = user_data.get('location', '全国')
        social_security = user_data.get('social_security', '城镇职工')
        
        # 风险映射
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
• 地区/社保类型：{location}/{social_security}

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
        return f"生成本地报告时出错：{str(e)}"

# 健康检查
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "养老金规划系统",
        "timestamp": datetime.now().isoformat()
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return "页面不存在", 404

@app.errorhandler(500)
def internal_error(error):
    return "服务器内部错误", 500

if __name__ == '__main__':
    print("="*80)
    print("养老金规划系统启动")
    print(f"项目根目录: {BASE_DIR}")
    print(f"本地访问: http://localhost:5000")
    print("="*80)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
