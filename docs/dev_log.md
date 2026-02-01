# 开发过程记录

## 2026-02-01

### 步骤 1：初始化最小项目骨架
- 目标：建立基础目录与最小 CLI 入口，确保项目可运行。
- 改动：创建 `src/`, `tests/`, `configs/`, `docs/`, `scripts/`；新增 `src/main.py`。
- 验证：`python3 -m src.main` 输出 `Mini-agent skeleton ready.`

### 步骤 2：提供最小配置样例
- 目标：提供 OpenRouter 配置样例，便于用户配置环境变量。
- 改动：新增 `configs/.env.example`，包含 `OPENROUTER_API_KEY` 与 `OPENROUTER_BASE_URL`。
- 验证：无需运行，仅检查文件存在与内容正确。

### 步骤 3：最小配置读取（环境变量）
- 目标：从环境变量读取 OpenRouter 配置，缺失 key 时给出清晰报错。
- 改动：更新 `src/main.py`，新增 `load_config()` 并在缺少 `OPENROUTER_API_KEY` 时退出。
- 验证：待运行（需设置 `OPENROUTER_API_KEY`）。

### 步骤 4：支持从 .env 读取配置
- 目标：默认加载项目根目录 `.env`，便于本地配置 API key。
- 改动：在 `src/main.py` 新增 `load_dotenv()`，在读取配置前加载 `.env`。
- 验证：待运行（需创建 `.env` 并设置 `OPENROUTER_API_KEY`）。
- 验证：`python3 -m src.main` 输出 `Mini-agent config loaded.`（确保 `.env` 在项目根目录）。

### 步骤 5：最小 OpenRouter 模型调用封装
- 目标：封装一次最小的 Chat Completions 调用并在 CLI 中验证输出。
- 改动：新增 `src/openrouter_client.py`；更新 `src/main.py` 调用模型并输出结果。
- 验证：待运行（需设置 `OPENROUTER_MODEL` 可选，默认 `openrouter/auto`）。

### 步骤 6：改用 requests 进行 HTTP 调用
- 目标：用轻量库简化网络请求，保留自写 agent 逻辑。
- 改动：新增 `requirements.txt`（仅 `requests`）；更新 `src/openrouter_client.py` 以 `requests` 实现。
- 验证：待运行（需安装依赖）。

- 说明：由于 pip 无法联网安装（DNS 失败），改用系统 Python 自带的 `requests`（2.31.0）进行验证。

### 步骤 7：调整验证用 prompt
- 目标：用更直观的中文输出进行模型调用验证。
- 改动：更新 `src/main.py` 的 prompt 为输出 “你好”。
- 验证：待运行。
- 验证：模型调用失败，DNS 无法解析 `openrouter.ai`（当前环境无外网或 DNS 被阻断）。
- 排查：WSL DNS 配置导致解析失败，临时改为 1.1.1.1 后可解析 `openrouter.ai`。

### 步骤 8：支持从 CLI 传入 prompt
- 目标：让用户通过命令行参数输入提示词。
- 改动：更新 `src/main.py`，使用 `sys.argv` 读取 prompt（默认保持“你好”）。
- 验证：待运行（本地可用 `python3 -m src.main "你好"`）。
- 验证：`python3 -m src.main "你好，今天天气怎么样？"` 正常返回模型输出。

### 步骤 9：引入 messages 结构与 system 提示
- 目标：展示基本对话消息结构（system/user）。
- 改动：更新 `src/openrouter_client.py` 接收 `messages`；`src/main.py` 组装 system + user 消息。
- 验证：待运行。

### 步骤 10：增加调试日志开关
- 目标：在需要时打印发送给模型的 messages，便于确认 system/user 是否传入。
- 改动：`src/main.py` 支持 `DEBUG=1` 时输出 messages。
- 验证：待运行（示例：`DEBUG=1 python3 -m src.main "你好"`）。
- 验证：`DEBUG=1 python3 -m src.main "你好"` 输出 messages 与正常模型回复。

### 步骤 11：加入对话记忆（多轮）
- 目标：在单次运行中保持历史 messages，实现多轮对话。
- 改动：`src/main.py` 增加循环输入与 `history`，每轮追加 user/assistant。
- 验证：待运行（输入 `exit` 退出）。
- 验证：多轮对话正常，`DEBUG=1` 显示 history 按顺序追加，模型能根据历史回答“第一句话”。

### 步骤 12：加入最小工具调用（calculator）
- 目标：演示“工具调用”如何接入循环，不经模型直接返回结果。
- 改动：`src/main.py` 增加 `calc:` 前缀检测与安全算术解析（`ast`）。
- 验证：待运行（示例：`calc: 1+2*3`）。

### 步骤 13：抽离工具定义与注册表
- 目标：避免工具逻辑堆在 `main.py`，为模型触发版做结构准备。
- 改动：新增 `src/tools.py`（工具协议 `ToolSpec`、`calculator` 规范、`eval_math_expr`）；`src/main.py` 改为导入工具函数。
- 验证：待运行（功能不变）。

### 步骤 14：向模型传递工具定义
- 目标：让模型“知道有哪些工具”，为工具触发做准备。
- 改动：`src/tools.py` 增加 `tool_specs()`；`src/openrouter_client.py` 支持 `tools` 参数；`src/main.py` 调用时传入工具定义。
- 验证：待运行（功能表现暂不变）。

### 步骤 15：DEBUG 输出工具定义
- 目标：在调试时看到传给模型的 tools 结构。
- 改动：`src/main.py` 在 `DEBUG=1` 时打印 `tool_specs()`。
- 验证：待运行。

### 步骤 16：简化 DEBUG 输出
- 目标：调试输出更直观，减少多行打印。
- 改动：`src/main.py` 将 messages/tools 合并为单行 `DEBUG payload` 输出。
- 验证：待运行。

### 步骤 17：解析模型返回的工具调用
- 目标：从模型响应中识别 `tool_calls` 并执行对应工具，再把结果回喂模型。
- 改动：`src/openrouter_client.py` 返回完整 JSON；`src/tools.py` 增加 `execute_tool()`；`src/main.py` 解析 `tool_calls`、执行工具、追加 `tool` 消息并进行二次调用。
- 验证：待运行（示例：询问需要计算的内容，让模型触发 calculator）。

### 步骤 18：完善工具调用调试日志
- 目标：清晰打印 tool_calls 与二次调用的 payload。
- 改动：`src/main.py` 增加 `DEBUG tool_calls` 与 `DEBUG followup_payload` 输出。
- 验证：待运行。

### 步骤 19：将 payload 日志移动到模型调用层
- 目标：每次模型调用都自动输出 payload，避免在 main 中遗漏。
- 改动：`src/openrouter_client.py` 在 `DEBUG=1` 时打印完整 payload；`src/main.py` 移除手动 payload 打印，仅保留 tool_calls/tool_results。
- 验证：待运行。
- 验证：DEBUG 日志显示每次模型调用的 payload（含 tools），tool_calls 触发 calculator 后二次调用正常返回结果。

### 步骤 20：细化工具描述
- 目标：明确 calculator 的参数范围与可支持的表达式。
- 改动：`src/tools.py` 更新 calculator 描述，说明支持的运算符与括号。
- 验证：待运行（仅描述变更）。

### 步骤 21：系统提示加入工具使用约束
- 目标：要求模型不要预计算表达式，避免绕过工具限制。
- 改动：`src/main.py` 更新 system 提示词。
- 验证：待运行。

### 步骤 22：DEBUG 输出模型完整响应
- 目标：在调试模式下查看模型返回的完整 JSON。
- 改动：`src/openrouter_client.py` 在 `DEBUG=1` 时打印 `DEBUG response`。
- 验证：待运行。

### 步骤 23：支持模型返回 JSON 代码块的工具调用
- 目标：兼容模型将工具调用写在文本中的情况。
- 改动：`src/main.py` 增加 `_parse_json_tool_call()`，当响应包含 ```json``` 且 method=calculator 时执行工具。
- 验证：待运行。

### 步骤 24：强化 system 提示词以强制 tool_calls
- 目标：尽量减少模型用纯文本 JSON 伪装工具调用。
- 改动：`src/main.py` system 提示词明确要求“必须用 tool_calls”。
- 验证：待运行。

### 步骤 25：精简调试日志输出
- 目标：只显示本轮新增 messages，并简化模型响应日志。
- 改动：`src/main.py` 仅打印当前轮的新增 messages；`src/openrouter_client.py` 仅打印响应 message 与 tool_calls。
- 验证：待运行。

### 步骤 26：请求时输出工具列表
- 目标：在 DEBUG 请求日志中包含工具列表。
- 改动：`src/main.py` 在 `DEBUG new_messages` 后打印 `DEBUG tools`。
- 验证：待运行。

### 步骤 27：兼容模型返回的“内联 tool call”格式
- 目标：当模型把 tool call 放在 content 里（JSON 列表/对象）时也能执行。
- 改动：`src/main.py` 增加 `_parse_inline_tool_call()`，在无 `tool_calls` 时解析内容并执行。
- 验证：待运行。

### 步骤 28：新增文件读写工具
- 目标：提供最小的 `read_file` 与 `write_file` 工具能力。
- 改动：`src/tools.py` 新增工具规范与执行逻辑；限制路径必须在项目根目录内。
- 验证：待运行（示例：读取 `src/main.py`）。

### 步骤 29：调试日志只显示本次工具结果
- 目标：避免 DEBUG tool_results 打印历史所有工具结果。
- 改动：`src/main.py` 只记录并打印本轮 `current_tool_results`。
- 验证：待运行。

### 步骤 30：更新默认模型配置
- 目标：将 OpenRouter 模型切换为 `google/gemini-2.0-flash-lite-001`（通过 `.env`）。
- 改动：更新 `.env` 中 `OPENROUTER_MODEL`。
- 验证：待运行（带 DEBUG 查看 payload 的 model）。

### 步骤 31：支持多轮连续工具调用
- 目标：当模型在 follow-up 中继续触发工具（如 read_file → write_file）时能正确执行。
- 改动：`src/main.py` 将单次 tool_call 处理改为循环，最多 3 轮工具调用。
- 验证：待运行（示例：要求读取后再写入文件）。

### 步骤 32：提高工具调用轮数上限
- 目标：允许更复杂的多步工具链。
- 改动：`src/main.py` 将 `max_tool_rounds` 调整为 15。
- 验证：无需运行。

### 步骤 33：新增 edit_file 工具
- 目标：提供最小可控的局部编辑能力。
- 改动：`src/tools.py` 新增 `edit_file`（替换首个匹配片段），并加入工具注册。
- 验证：待运行（示例：替换 `docs/dev_log.md` 中一小段文本）。

### 步骤 34：edit_file 支持差异预览与确认
- 目标：在应用编辑前展示 diff，并要求用户确认。
- 改动：`src/tools.py` 新增 `preview_edit`/`apply_edit`，更新 `edit_file` 描述；`src/main.py` 在执行 `edit_file` 时先预览并询问确认。
- 验证：待运行（示例：替换 `docs/dev_log.md` 的标题）。

### 步骤 35：加强文件编辑流程约束
- 目标：要求编辑前读取文件，编辑后再次读取验证。
- 改动：`src/main.py` system 提示词增加读前/读后要求。
- 验证：待运行。

### 步骤 36：新增 run_shell 工具
- 目标：允许模型在项目根目录执行命令并返回 stdout/stderr。
- 改动：`src/tools.py` 新增 `run_shell` 工具与执行逻辑（超时 30 秒）。
- 验证：待运行（示例：`ls` 或 `git status`）。
