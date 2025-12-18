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
    调用Dify工作流
    Args:
        user_data: 用户输入的数据字典

    Returns:
        Dify API的响应结果
    """
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    # 构建Dify请求体
    payload = {
        "inputs": user_data,
        "response_mode": "blocking",  # 同步模式
        "user": f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }

    try:
        print(f"调用Dify工作流: {WORKFLOW_ID}")
        print(f"用户数据: {user_data}")

        response = requests.post(
            f"{DIFY_API_URL}/{WORKFLOW_ID}",
            headers=headers,
            json=payload,
            timeout=60
        )

        print(f"Dify响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Dify响应成功")
            return result
        else:
            print(f"Dify API错误: {response.status_code} - {response.text}")
            return {
                "error": True,
                "message": f"Dify API错误: {response.status_code}",
                "details": response.text
            }

    except requests.exceptions.Timeout:
        print("Dify API调用超时")
        return {
            "error": True,
            "message": "请求超时，请稍后重试"
        }
    except Exception as e:
        print(f"调用Dify失败: {str(e)}")
        return {
            "error": True,
            "message": f"系统错误: {str(e)}"
        }


@app.route('/')
def index():
    """首页 - 显示输入表单"""
    # 初始化会话
    session['session_id'] = str(uuid.uuid4())[:8]
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit_form():
    """处理表单提交"""
    try:
        # 获取表单数据
        form_data = request.form.to_dict()

        # 验证必要字段
        required_fields = ['age', 'annual_income', 'risk_tolerance']
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                return jsonify({
                    "success": False,
                    "message": f"请填写{field}字段"
                })

        # 转换数据类型
        user_data = {
            "age": int(form_data.get('age', 30)),
            "annual_income": float(form_data.get('annual_income', 20.0)),
            "risk_tolerance": form_data.get('risk_tolerance', '中'),
            "location": form_data.get('location', '全国'),
            "social_security": form_data.get('social_security', '城镇职工'),
            "retirement_age": int(form_data.get('retirement_age', 60)),
            "investment_amount": float(form_data.get('investment_amount', 10.0))
        }

        # 可选高级选项
        if form_data.get('insurance_type') and form_data.get('insurance_type') != '全部':
            user_data['filter_criteria'] = {
                "insurance_type": form_data.get('insurance_type')
            }

        # 调用Dify工作流
        dify_result = call_dify_workflow(user_data)

        if dify_result and 'error' not in dify_result:
            # 保存到会话
            session['user_data'] = user_data
            session['dify_result'] = dify_result
            session['submission_time'] = datetime.now().isoformat()

            return jsonify({
                "success": True,
                "message": "分析完成！",
                "redirect": "/results"
            })
        else:
            error_msg = dify_result.get('message', '未知错误') if dify_result else 'Dify响应为空'
            return jsonify({
                "success": False,
                "message": f"分析失败: {error_msg}"
            })

    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"数据格式错误: {str(e)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"系统错误: {str(e)}"
        })


@app.route('/results')
def show_results():
    """显示分析结果"""
    if 'dify_result' not in session:
        return "没有找到分析结果，请先提交表单。", 400

    user_data = session.get('user_data', {})
    dify_result = session.get('dify_result', {})

    return render_template('results.html',
                           user_data=user_data,
                           dify_result=dify_result)


@app.route('/api/test')
def test_api():
    """测试Dify连接"""
    test_data = {
        "age": 35,
        "annual_income": 25.0,
        "risk_tolerance": "中",
        "location": "北京",
        "social_security": "城镇职工",
        "retirement_age": 60,
        "investment_amount": 12.0
    }

    result = call_dify_workflow(test_data)
    return jsonify(result)


@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "养老金规划Web应用",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("养老金规划Web应用启动中...")
    print(f"DIFY_API_KEY: {'已设置' if DIFY_API_KEY else '未设置'}")
    print(f"WORKFLOW_ID: {'已设置' if WORKFLOW_ID else '未设置'}")
    print("本地访问: http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)