import webbrowser
from datetime import datetime
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Qsever 解题结果</title>
  <script>
    MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']]
      }
    };
  </script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
      max-width: 900px;
      margin: 0 auto;
      padding: 30px 20px;
      background: #fafafa;
      color: #333;
      line-height: 1.8;
    }
    h1 {
      color: #2196F3;
      border-bottom: 3px solid #2196F3;
      padding-bottom: 10px;
    }
    .timestamp {
      color: #888;
      font-size: 0.9em;
      margin-bottom: 30px;
    }
    .section {
      background: white;
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .question {
      border-left: 4px solid #2196F3;
    }
    .answer {
      border-left: 4px solid #4CAF50;
    }
    .section h3 {
      margin-top: 0;
      color: #555;
    }
    .question h3 { color: #2196F3; }
    .answer h3 { color: #4CAF50; }
    pre {
      background: #f5f5f5;
      padding: 15px;
      border-radius: 4px;
      overflow-x: auto;
    }
    code {
      font-family: "Consolas", "Monaco", monospace;
      background: #f0f0f0;
      padding: 2px 6px;
      border-radius: 3px;
    }
    pre code {
      background: none;
      padding: 0;
    }
    .footer {
      text-align: center;
      color: #aaa;
      font-size: 0.85em;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }
  </style>
</head>
<body>
  <h1>Qsever 解题结果</h1>
  <div class="timestamp">生成时间：__TIMESTAMP__</div>

  <div class="section question">
    <h3>题目</h3>
    <div>__QUESTION__</div>
  </div>

  <div class="section answer">
    <h3>解答</h3>
    <div>__ANSWER__</div>
  </div>

  <div class="footer">
    由 Qsever 高中解题助手生成 | MathJax 渲染数学公式
  </div>
</body>
</html>"""


class HTMLExporter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, question: str, answer: str, timestamp: str | None = None) -> Path:
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html_content = HTML_TEMPLATE.replace("__TIMESTAMP__", timestamp)
        html_content = html_content.replace("__QUESTION__", self._escape_html(question))
        html_content = html_content.replace("__ANSWER__", self._markdown_to_html(answer))

        safe_timestamp = timestamp.replace(":", "-").replace(" ", "_")
        filename = f"qsever_{safe_timestamp}.html"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return filepath

    def open_in_browser(self, filepath: Path):
        webbrowser.open(f"file:///{filepath.absolute()}")

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _markdown_to_html(self, text: str) -> str:
        lines = text.split("\n")
        html_lines = []
        in_code_block = False
        code_block_lang = ""

        for line in lines:
            if line.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_block_lang = line[3:].strip()
                    html_lines.append(f'<pre><code class="{code_block_lang}">')
                else:
                    in_code_block = False
                    html_lines.append("</code></pre>")
                continue

            if in_code_block:
                html_lines.append(self._escape_html(line))
                continue

            if line.startswith("### "):
                html_lines.append(f"<h4>{line[4:]}</h4>")
            elif line.startswith("## "):
                html_lines.append(f"<h3>{line[3:]}</h3>")
            elif line.startswith("# "):
                html_lines.append(f"<h2>{line[2:]}</h2>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<p><strong>{line[2:-2]}</strong></p>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.strip() == "":
                html_lines.append("<br>")
            else:
                html_lines.append(f"<p>{line}</p>")

        return "\n".join(html_lines)
