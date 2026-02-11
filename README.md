# US Stock Quant System

美股量化交易系统：历史回测、IBKR 实盘/模拟盘、全栈可视化。

## 技术栈

- **后端核心**: Python 3.11+, Pandas, NumPy, Pydantic
- **交易接口**: ib_insync (Interactive Brokers)
- **Web 后端**: FastAPI
- **Web 前端**: React (Vite), Tailwind CSS, Lightweight-charts
- **存储**: CSV (历史/回测), JSON (实盘状态)

## 目录结构

```
/QuantSystem
├── config/           # 统一配置 config.properties (default.* / available.*)
├── store/            # 数据中心 (market_data, backtest_results, live_state)
├── core/             # 类型、配置与 properties 解析
├── skills/           # IB 客户端
├── data/             # 数据加载与更新
├── strategies/       # 策略（分买入/卖出，多策略可组合）
│   ├── buy/          # 买入策略 (仅 BUY/HOLD)，如 oversold_score_buy
│   └── sell/         # 卖出策略 (仅 SELL/HOLD)，如 stop_loss_8pct_sell, boll_upper_break_sell
├── backtest/         # 回测引擎
├── live/             # 实盘守护进程
├── web/backend/     # FastAPI
├── web/frontend/     # React
└── scripts/          # 脚本 (如 run_backtest.py)
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
cd web/frontend && npm install
```

### 2. 运行回测（生成示例结果）

**配置** 在 **`config/config.properties`**（`default.*` / `available.*` 格式）：
- **default.buy**：买入策略，逗号分隔，需**全部命中**才买；当前为 `oversold_score_buy`（超卖买入）。
- **default.sell**：卖出策略，逗号分隔，**任一命中**即卖；当前为 `stop_loss_8pct_sell`（固定比例止损）、`trailing_take_profit_sell`（移动止盈）、`boll_upper_break_sell`（突破上布林带）、`two_day_no_profit_sell`（买入后两天不盈利卖出）。
- **default.start_date** / **default.end_date**：回测区间。

```bash
python scripts/run_backtest.py
```

### 3. 启动 Web

**一键起停**（项目根目录执行）:

```bash
./web/start.sh   # 启动后端 (8000) + 前端 (5173)，日志在 web/logs/
./web/stop.sh    # 停止
```

或分别启动：

```bash
uvicorn web.backend.main:app --reload --host 0.0.0.0 --port 8000
cd web/frontend && npm run dev
```

浏览器打开 http://localhost:5173，前端会代理 `/api` 到 8000 端口。

### 4. 实盘（可选）

- 在 `config/config.properties` 中配置 `ib.*`（端口、账户等）；或沿用 `core/config.py` 中的 IB 配置。
- 运行 `live/trader.py` 守护进程；状态写入 `store/live_state/*.json`，仪表盘自动读取。

## API 说明

- `GET /api/market/kline/{symbol}` 日 K 线
- `GET /api/backtest/list` 回测列表
- `GET /api/backtest/detail/{id}` 回测详情（资金曲线 + 交割单）
- `GET /api/live/snapshot` 实盘快照

## 开发说明

- 策略只接收数据、只输出信号，不下单。
- 回测结果与实盘状态均通过 `/store` 文件与 Web 解耦。
