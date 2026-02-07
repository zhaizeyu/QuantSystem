
# US Stock Quant System - Product Requirement Document (PRD)

## 1. 项目概览 (Project Overview)

构建一个现代化的美股量化交易系统。系统需具备**历史数据回测**、**IBKR 实盘/模拟盘交易**以及**全栈可视化监控**功能。

核心设计理念是**“逻辑与展示分离”**：Python 后端负责核心计算与交易，通过文件系统 (`/store`) 与 Web 端解耦。

## 2. 技术栈 (Tech Stack)

- **Core Backend:** Python 3.11+, Pandas, NumPy, Pydantic.
    
- **Trading Interface:** `ib_insync` (Interactive Brokers API).
    
- **Web Backend:** FastAPI (读取数据提供 API).
    
- **Web Frontend:** React (Vite), Tailwind CSS, shadcn/ui.
    
- **Charting:** Lightweight-charts (TradingView).
    
- **Storage:** CSV (历史数据/回测记录), JSON (实盘状态).
    

## 3. 系统目录结构 (Directory Structure)

_请 AI 严格遵守此结构进行文件创建。_

```
/QuantSystem
├── /config                 # [统一配置]
│   └── config.properties   # default.* / available.* 格式，策略名、日期、资金等
│
├── /store                  # [数据中心 - 文件数据库]
│   ├── /market_data        # CSV: 历史日K数据 (e.g., AAPL_daily.csv)
│   ├── /backtest_results   # CSV: 回测交割单与资金曲线 (bt_*_*.csv, *_equity.csv)
│   └── /live_state         # JSON: 实盘实时状态 (account.json, positions.json)
│
├── /core                   # [核心定义]
│   ├── types.py            # Pydantic Models (Bar, Signal, TradeRecord)
│   ├── config.py           # 全局路径与配置入口
│   ├── properties_loader.py # 解析 config.properties
│   └── backtest_config.py  # 回测默认参数 (从 default.* 读取)
│
├── /skills                 # [能力层 - 外部交互]
│   └── ib_client.py        # 封装 IBKR 连接、下单、查持仓
│
├── /data                   # [数据处理]
│   └── loader.py           # 读取/清洗 CSV，更新 CSV
│
├── /strategies             # [策略层 - 纯逻辑，由 config 驱动]
│   ├── base.py             # 策略基类
│   ├── indicators.py       # RSI、布林带、MACD 等指标
│   ├── factory.py          # 根据配置名称创建买入/卖出策略实例
│   ├── /buy                # 买入策略 (仅 BUY/HOLD)，如 oversold_score_buy
│   └── /sell               # 卖出策略 (仅 SELL/HOLD)，如 stop_loss_8pct_sell, boll_upper_break_sell
│
├── /backtest               # [回测引擎]
│   └── engine.py           # 多策略组合：买入全部命中才买，卖出任一命中即卖
│
├── /live                   # [实盘引擎]
│   └── trader.py           # 实盘主循环 (Daemon Process)
│
├── /web                    # [可视化系统]
│   ├── /backend            # FastAPI (main.py, routers)
│   └── /frontend           # React (Vite), KlineChart, TradeTable, Dashboard, BacktestLab
│
└── /scripts                # 脚本
    └── run_backtest.py     # 从 config 读取 default 并执行回测
```

---

## 4. 核心数据模型 (Core Schemas)

_定义在 `core/types.py` 中。这是系统的“法律”。_

### 4.1 `Bar` (K线数据)

date,open,high,low,close,volume,average,barCount
    

### 4.2 `Signal` (策略输出)

- `action`: Enum (BUY, SELL, HOLD)
    
- `strength`: float (0.0 - 1.0, 信号强度)
    
- `reason`: str (关键！例如: "超卖买入", "突破上布林带", "止损8%")
    

### 4.3 `TradeRecord` (详细交割单 - 回测与实盘共用)

_需包含用户要求的详细字段。_

- `trade_id`: str (UUID)
    
- `timestamp`: datetime
    
- `symbol`: str
    
- `side`: str (BUY/SELL)
    
- `price`: float (成交均价)
    
- `quantity`: int (成交数量)
    
- `commission`: float (手续费)
    
- `strategy_name`: str (策略名称)
    
- **`entry_reason`: str** (开仓原因，来自 Signal)
    
- **`exit_reason`: str** (平仓原因，如 "止损8%", "突破上布林带")
    
- **`pnl`: float** (平仓时计算盈亏金额，开仓为 0)
    
- **`roi`: float** (平仓时计算收益率 %)
    
- **`holdings_after`: int** (成交后该股剩余持仓)
    

---

## 5. 模块详细规格 (Module Specifications)

### 5.1 数据模块 (`data`)

- **Loader:** 提供 `get_bars(symbol, start, end)` 函数，返回 DataFrame。
    
- **Updater:** 提供 `update_history(symbol)` 函数，调用 `skills.ib_client` 获取最新日 K 并追加到 `/store/market_data/*.csv`。
    

### 5.2 策略模块 (`strategies`)

- **解耦原则:** 策略**只接收数据，只输出信号**，绝对不直接下单。
    
- **结构:** 买入策略在 `strategies/buy/`，卖出策略在 `strategies/sell/`；通过 `config.properties` 的 `default.buy` / `default.sell` 配置名称，由 `factory.py` 创建实例。
    
- **多策略组合:** 回测时**多个买入策略需全部命中才下单**，**多个卖出策略任一命中即卖出**；卖出策略可接收 `position_avg_cost`、`current_price` 等 kwargs 用于止损等逻辑。
    
- **输入:** `current_bar`, `history_df`, `current_position`；卖出策略另有 kwargs（如持仓成本、现价）。
    
- **输出:** `Signal` 对象 (action, strength, reason)。
    

### 5.3 回测模块 (`backtest`)

- **流程:**
    
    1. 初始化虚拟资金 (e.g., $100k)。
        
    2. 加载 CSV 数据，转换为 DataFrame。
        
    3. **逐行遍历 (Event Loop):**
        
        - 将切片数据传给策略。
            
        - 接收 Signal。
            
        - 模拟撮合 (考虑滑点与手续费)。
            
        - 生成 `TradeRecord`。
            
    4. **计算绩效:** 总收益、最大回撤、夏普比率。
        
    5. **持久化:** 将 `List[TradeRecord]` 保存为 CSV 到 `/store/backtest_results`。
        

### 5.4 实盘/模拟盘模块 (`live`)

- **守护进程:** `trader.py` 是一个 `while True` 循环。
    
- **职责:**
    
    1. 维护 IB 连接。
        
    2. 每分钟拉取最新 K 线。
        
    3. 运行策略。
        
    4. **风控检查:** (例如: 单笔亏损不超过总资金 1%)。
        
    5. 执行交易。
        
    6. **状态导出:** 每 5 秒将 `AccountSummary` 和 `Positions` 写入 `/store/live_state/*.json` 供 Web 端读取。
        

---

## 6. Web 可视化规格 (Web Specifications)

### 6.1 后端 API (FastAPI)

- `GET /api/market/kline/{symbol}`: 读取 CSV 返回 OHLC 数据。
    
- `GET /api/backtest/list`: 列出所有回测记录文件。
    
- `GET /api/backtest/detail/{id}`: 返回某次回测的**资金曲线**和**完整交割单**。
    
- `GET /api/live/snapshot`: 读取 JSON 返回实盘账户状态。
    

### 6.2 前端界面 (React)

#### **页面 1: 实盘仪表盘 (Live Dashboard)**

- **资产卡片:** 展示总资产 (Net Liquidation Value)、日内盈亏 (Unrealized PnL)。
    
- **持仓表格:** 代码 | 数量 | 成本价 | 现价 | 浮动盈亏 | **操作(一键平仓按钮)**。
    

#### **页面 2: 回测分析 (Backtest Lab)**

- **图表区:**
    
    - 主图: K线图 + **买卖标记 (Markers)** (鼠标悬停显示 `reason`)。
        
    - 副图: 资金曲线 (Equity Curve)。
        
- **交割单表格:**
    
    - 展示所有 `TradeRecord`。
        
    - 列: 时间, 代码, 方向, 价格, **策略原因**, **收益率(ROI)**, 累计收益。
        
    - 支持按 ROI 排序 (快速复盘亏损单)。
        

---

## 7. AI 开发指令指南 (Developer Guide for AI)

请按照以下顺序生成代码，每一步完成后都需要进行测试：

1. **Phase 1: Foundation**
    
    - 创建目录结构。
        
    - 实现 `core/types.py` (Pydantic Models)。
        
    - 实现 `data/loader.py` (CSV 读写)。
        
2. **Phase 2: Strategy & Backtest**
    
    - 实现 `strategies/buy/`、`strategies/sell/` 下的策略（如超卖买入、止损、突破上布林带卖出），以及 `strategies/indicators.py`、`strategies/factory.py`。
        
    - 实现 `backtest/engine.py`（支持多买入/多卖出策略组合）。
        
    - 统一配置放在 `config/config.properties`（`default.buy` / `default.sell` / 日期等）。
        
    - **验证:** 运行 `scripts/run_backtest.py`，在 `/store/backtest_results` 生成包含 `entry_reason`、`exit_reason`、`roi` 的 CSV。
        
3. **Phase 3: Web Visualization**
    
    - 搭建 FastAPI，写接口读取 Phase 2 生成的 CSV。
        
    - 搭建 React，写 `KlineChart` 组件，确保能把买卖点画在 K 线上。
        
4. **Phase 4: Live Trading Integration**
    
    - 实现 `skills/ib_client.py`。
        
    - 编写 `live/trader.py` 主循环。
        

