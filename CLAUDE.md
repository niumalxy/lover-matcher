# Lover-Matcher 项目规范

恋爱匹配平台 MVP。微信小程序前端 + Python 后端，数据用本地 CSV 存储。业务需求详见 `prd.txt`。

本规范是项目长期约束，所有代码改动必须遵守。修改本规范需先告知用户。

---

## 一、目录结构

```
lover-matcher/
├── backend/                       # Python 后端
│   ├── conf/
│   │   ├── conf.yml               # LLM provider 配置（含 key，不入版本库）
│   │   └── runtime.json           # 运行时可变配置（如当前默认 provider），程序写入
│   ├── app/
│   │   ├── api/                   # FastAPI 路由层，按业务域分文件
│   │   │   ├── matchee.py         # 被匹配端接口
│   │   │   ├── matcher.py         # 匹配端接口
│   │   │   ├── chat.py            # 与智能恋爱助手对话
│   │   │   └── admin.py           # 后台管理（切换 LLM 等）
│   │   ├── services/              # 业务逻辑层
│   │   │   ├── profile.py         # 画像/择偶标准提取
│   │   │   ├── matcher_agent.py   # 智能恋爱助手对话与匹配判定
│   │   │   └── candidate.py       # 候选池
│   │   ├── storage/               # CSV 读写适配
│   │   │   ├── base.py            # 通用 CSV 操作 + 文件锁
│   │   │   ├── users.py
│   │   │   ├── profiles.py
│   │   │   ├── conversations.py
│   │   │   └── matches.py
│   │   ├── llm/
│   │   │   ├── client.py          # 统一调用入口（chat / vision）
│   │   │   └── registry.py        # 读取 conf.yml + runtime.json
│   │   ├── prompts/               # 提示词模板（每场景一个文件）
│   │   ├── models/                # Pydantic 模型（请求/响应/领域对象）
│   │   ├── admin_web/             # 后台管理静态页（极简 HTML，由 FastAPI 托管）
│   │   └── main.py                # FastAPI 入口
│   ├── data/                      # 运行时数据，不入版本库
│   │   ├── *.csv
│   │   └── uploads/               # 用户头像
│   └── requirements.txt
├── miniprogram/                   # 微信小程序前端
│   ├── pages/
│   │   ├── matchee/               # 被匹配端页面
│   │   └── matcher/               # 匹配端页面
│   ├── components/                # 复用组件
│   ├── services/                  # 后端 API 调用封装（不在页面里直接 wx.request）
│   ├── utils/
│   ├── app.ts / app.json / app.wxss
├── prd.txt
└── CLAUDE.md                      # 本规范
```

新增模块必须按上述分层归类，不要散落在根目录或某一层的杂项文件夹。

---

## 二、后端规范

### 技术选型（已确定）
- Python ≥ 3.10
- 依赖管理：**uv**（`pyproject.toml` + `uv.lock`）；安装 `uv sync`，加依赖 `uv add <pkg>`，跑命令 `uv run <cmd>`。不再用 `pip` / `requirements.txt`
- Web 框架：**FastAPI**（自带 Pydantic 校验 + OpenAPI 文档）
- 数据：CSV，每个业务实体一个文件
- LLM SDK：openai 兼容客户端（conf.yml 里所有 provider 都走 OpenAI 协议）

### 分层职责（不允许跨层调用）
- `api/`：接收请求 → 参数校验 → 调用 service → 返回响应；不写业务逻辑
- `services/`：业务规则、流程编排；不直接读写 CSV，不直接调 LLM SDK
- `storage/`：CSV 细节封装，对上暴露领域操作（`get_user(id)`、`add_match(...)`），不写业务规则
- `llm/`：所有 LLM 调用必须经此层；service 通过 `llm.client.chat(...)` 调用

跨层调用示例 ✗：`api` 直接读 CSV、`service` 直接调 `openai.ChatCompletion`。

### 代码风格
- PEP 8，4 空格缩进
- 函数签名、领域模型必须有类型注解
- 模块/函数 snake_case，类 PascalCase，常量 UPPER_SNAKE_CASE
- 用 `logging`，不用 `print`
- 业务错误抛自定义异常（`app/errors.py`），统一异常中间件转 HTTP 响应

### CSV 存储约定
- 所有 CSV 在 `backend/data/`，UTF-8，逗号分隔，首行表头
- **写操作必须加文件锁**（用 `filelock` 库），避免并发损坏
- 主键统一字段名 `id`，类型 UUID4 字符串
- 字段含结构化数据（如择偶标准 JSON）时，单元格存 JSON 字符串
- 列结构变更需同步更新 `storage/` 里的常量定义和已有数据迁移脚本

### LLM 调用约定
- 统一入口：`app/llm/client.py` 的 `chat(messages, provider=None)` / `vision(...)`
- `provider=None` 时使用「当前默认 provider」（见下一节后台管理）
- conf.yml 列出可用 provider 及其 key/endpoint/model；新增 provider 改 conf.yml 即可
- 提示词放 `app/prompts/`，按场景命名（`profile_extract.txt`、`matcher_agent.txt`），代码里加载模板，不在代码里拼长 prompt

### 后台管理（admin）
- 默认 LLM provider 不写死，存于 `conf/runtime.json`，可通过 admin 接口实时切换
- 提供极简管理页 `app/admin_web/index.html`（原生 HTML + fetch，无前端框架），由 FastAPI 静态托管在 `/admin`
- 鉴权：MVP 用环境变量 `ADMIN_TOKEN`，请求头 `X-Admin-Token` 校验；不做账号体系
- 至少提供：查看/切换默认 provider、查看候选池、查看配对记录

---

## 三、前端规范

### 沿用现有约定
- TypeScript strict（保留 `tsconfig.json`）
- 2 空格缩进
- 微信小程序原生框架，glass-easel，`style: v2`

### 目录与命名
- 页面按用户端分组：`pages/matchee/*`、`pages/matcher/*`
- 公共组件：`components/`，使用 PascalCase 文件名
- 文件/变量 camelCase；常量 UPPER_SNAKE_CASE

### 服务调用
- 所有后端调用走 `services/api.ts`（封装 wx.request、统一错误处理、注入 baseUrl）
- baseUrl 来自 `app.ts` 的 globalData，**不允许在页面/服务里硬编码**
- 不在页面 `.ts` 里直接 `wx.request`

### 现有示例页处理
- `pages/index` 和 `pages/logs` 是模板示例，**实现首页时直接替换 `pages/index` 内容为新首页**（按双端选择跳 matchee/matcher），`pages/logs` 可保留或删除

---

## 四、API 约定

- 路径前缀：`/api/v1/`
- REST 语义（GET 查 / POST 建 / PUT 改 / DELETE 删）
- 响应壳统一：
  ```json
  { "code": 0, "msg": "ok", "data": {...} }
  ```
  `code=0` 成功，非 0 失败；`msg` 给前端展示用
- 用户身份：MVP 用微信 `openid`
  - 前端 `wx.login` 拿 code，调后端 `/api/v1/auth/login` 换 openid
  - 后续请求头带 `X-OpenId`（MVP 简化，不做 session/JWT）
- 后台管理路径前缀 `/admin/api/`，请求头带 `X-Admin-Token`

---

## 五、敏感信息

- `backend/conf/conf.yml` 含真实 LLM API key，**任何情况下不得提交到公共仓库或外部共享**
- 启用 git 时，将以下加入 `.gitignore`：
  ```
  backend/conf/conf.yml
  backend/conf/runtime.json
  backend/data/
  ```
  并提供 `backend/conf/conf.example.yml` 模板（占位 key）
- 日志、错误响应、调试输出中绝不打印完整 key

---

## 六、MVP 边界（避免过度工程）

- 不引入数据库、缓存、消息队列
- 不做完整鉴权（openid + admin token 足够）
- 不写完整单元测试套件，仅对关键业务（画像提取、匹配判定）写少量校验脚本
- 不做国际化、主题切换、动画美化
- 不为「未来可能需要」写抽象层，等真正用到再加

---

## 七、协作约定（针对 Claude）

- 改本规范前先告知用户
- 引入新依赖（pip / npm 包）前先列出并说明用途
- 写代码前先列「将要修改/新建的文件清单」
- 不擅自改 `conf.yml` 中的 provider 列表或 key
- 遇到规范未覆盖的设计点，先问用户，不擅自决定
- 改 CSV 列结构必须同步更新 `storage/` 常量和数据迁移逻辑

---

## 八、已定决策（MVP）

1. **择偶标准编辑**：LLM 生成后展示在表单里，用户可直接编辑文本字段；通过对话二次精调放到 v2
2. **配对成功交换联系方式**：被匹配者单方同意即可（符合 prd 第 3 点字面），匹配者同步收到通知
3. **候选池过滤**：被匹配者注册时填「自身性别 + 期望性别」，候选池只展示符合期望性别的对象
4. **admin 入口形态**：浏览器访问 `/admin`，FastAPI 托管极简 HTML，`ADMIN_TOKEN` 鉴权（不做小程序内 admin）
