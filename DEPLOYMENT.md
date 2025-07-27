# GitHub Pages 部署指南

## 第一步：创建GitHub仓库

1. 在GitHub上创建新仓库，建议命名为 `daily-papers-site`
2. 将此目录的所有文件推送到仓库

```bash
# 在 github-pages-site 目录下执行
git init
git add .
git commit -m "Initial commit: Daily Papers Site"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/daily-papers-site.git
git push -u origin main
```

## 第二步：配置GitHub Pages

1. 进入仓库的 Settings → Pages
2. Source 选择 "GitHub Actions"
3. 保存设置

## 第三步：更新配置

### 1. 更新网站配置文件

编辑 `config.yml`，替换以下内容：

```yaml
site:
  url: "https://YOUR_USERNAME.github.io/daily-papers-site"  # 替换YOUR_USERNAME
  email: "your-email@example.com"  # 替换为您的邮箱
  github_repo: "https://github.com/YOUR_USERNAME/daily-papers-site"  # 替换YOUR_USERNAME
  main_project: "https://github.com/YOUR_USERNAME/daily-paper-v2"  # 替换YOUR_USERNAME
```

### 2. 更新模板中的链接

编辑 `templates/base.html` 和 `templates/about.html`，替换其中的链接。

### 3. 更新主项目配置

在主项目的配置文件中（如 `config/rag.yaml`），更新RSS设置：

```yaml
rss_site_url: "https://YOUR_USERNAME.github.io/daily-papers-site"
rss_feed_title: "Daily AI Papers"
rss_feed_description: "Latest papers in AI research"
```

## 第四步：测试部署

### 本地测试

```bash
# 创建示例数据
python scripts/process_papers.py --sample

# 构建网站
python scripts/build_site.py

# 查看生成的文件
ls public/
```

### 手动触发部署

1. 进入GitHub仓库的 Actions 页面
2. 选择 "Deploy to GitHub Pages" workflow
3. 点击 "Run workflow"

## 第五步：配置主项目推送

在主项目中，需要配置GitHub API调用来触发网站更新。

### 1. 创建GitHub Token

1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 生成新token，权限选择：
   - `repo` (完整仓库权限)
   - `workflow` (工作流权限)

### 2. 在主项目中添加部署节点

创建 `daily_paper/nodes/deploy_github_node.py`：

```python
import requests
from pocketflow import Node
from daily_paper.utils.logger import logger

class DeployGitHubNode(Node):
    def __init__(self, github_token, repo_owner, repo_name):
        super().__init__()
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
    
    def prep(self, shared):
        return {
            "html_files": shared.get("html_files", []),
            "date": shared.get("html_generation_date")
        }
    
    def exec(self, prep_res):
        if not prep_res.get("html_files"):
            return {"success": False, "reason": "No HTML files to deploy"}
        
        # 调用GitHub API触发部署
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/dispatches"
        
        payload = {
            "event_type": "publish_papers",
            "client_payload": {
                "html_files": prep_res["html_files"],
                "date": prep_res["date"]
            }
        }
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {"success": True, "response": response.status_code}
        except Exception as e:
            logger.error(f"GitHub API调用失败: {e}")
            return {"success": False, "error": str(e)}
    
    def post(self, shared, prep_res, exec_res):
        if exec_res.get("success"):
            shared["github_deployed"] = True
            logger.info("GitHub Pages部署触发成功")
        else:
            shared["github_deployed"] = False
            logger.error(f"GitHub Pages部署失败: {exec_res.get('error')}")
        
        return "default"
```

### 3. 更新Flow集成部署

在 `daily_paper_flow_v2.py` 中添加：

```python
from daily_paper.nodes import DeployGitHubNode

# 在创建节点部分添加
deploy_node = DeployGitHubNode(
    github_token=config.github_token,  # 需要在config中添加
    repo_owner=config.github_repo_owner,  # 需要在config中添加
    repo_name=config.github_repo_name   # 需要在config中添加
)

# 在流程连接部分
... >> publish_rss_node >> deploy_node
```

## 第六步：验证部署

1. 访问 `https://YOUR_USERNAME.github.io/daily-papers-site`
2. 检查RSS feed：`https://YOUR_USERNAME.github.io/daily-papers-site/rss.xml`
3. 使用RSS阅读器测试订阅

## 自定义域名（可选）

如果您有自己的域名：

1. 在仓库根目录创建 `CNAME` 文件，内容为您的域名
2. 在域名DNS设置中添加CNAME记录指向 `YOUR_USERNAME.github.io`
3. 更新 `config.yml` 中的 `site.url`

## 监控和维护

### 查看部署日志

1. GitHub仓库 → Actions
2. 查看最新的workflow运行记录

### 常见问题

1. **部署失败**：检查Actions日志，通常是权限或文件路径问题
2. **RSS无法访问**：确保 `public/rss.xml` 文件生成成功
3. **样式显示异常**：检查CSS文件路径和GitHub Pages设置

### 更新网站

网站会在以下情况自动更新：
1. 主项目推送新论文数据时
2. 手动触发GitHub Actions
3. 推送代码到main分支时

---

部署完成后，您的RSS地址将是：
```
https://YOUR_USERNAME.github.io/daily-papers-site/rss.xml
```