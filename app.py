import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

# 初始化 OpenAI 客户端（支持任何兼容接口，包括小米 MiMo）
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
)

SYSTEM_PROMPT = """你是小说地理学专家。根据用户提供的小说片段，提取其中的地理概念（大陆、海洋、城市、山脉等），并分析它们之间的空间关系（如“北部是”、“相邻”、“海峡相隔”等）。

输出格式：返回 JSON 对象，包含两个字段：
- "nodes": 每个地理实体的名称（去重）
- "links": 实体之间的关系，每一条格式为 {"source": "实体A", "target": "实体B", "label": "关系描述"}

同时，请结合自然地理知识（如海陆分布、气候带）合理推测缺失的地理关系。只输出 JSON，不要其他文字。"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate_map', methods=['POST'])
def generate_map():
    data = request.get_json()
    novel_text = data.get('novel_text', '').strip()
    if not novel_text:
        return jsonify({'error': '请提供小说文本'}), 400

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"小说内容：\n{novel_text[:3000]}"}  # 限制长度
            ],
            temperature=0.5,
        )
        result_text = response.choices[0].message.content
        # 提取 JSON
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0]
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0]
        map_data = json.loads(result_text)
        return jsonify(map_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
