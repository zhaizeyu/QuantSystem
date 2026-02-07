import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import BacktestLab from "./pages/BacktestLab";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-900 text-slate-200">
        <nav className="border-b border-slate-700 bg-slate-800/50 px-4 py-3 flex gap-6">
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive ? "text-amber-400 font-medium" : "text-slate-400 hover:text-slate-200"
            }
          >
            实盘仪表盘
          </NavLink>
          <NavLink
            to="/backtest"
            className={({ isActive }) =>
              isActive ? "text-amber-400 font-medium" : "text-slate-400 hover:text-slate-200"
            }
          >
            回测分析
          </NavLink>
        </nav>
        <main className="p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/backtest" element={<BacktestLab />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
