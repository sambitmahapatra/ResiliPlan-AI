import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/Layout";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Network from "./pages/Network";
import Scenarios from "./pages/Scenarios";
import Planning from "./pages/Planning";
import DataStudio from "./pages/DataStudio";
import Insights from "./pages/Insights";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

const shell = (el: JSX.Element) => <AppShell>{el}</AppShell>;

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={shell(<Dashboard />)} />
      <Route path="/network" element={shell(<Network />)} />
      <Route path="/planning" element={shell(<Planning />)} />
      <Route path="/scenarios" element={shell(<Scenarios />)} />
      <Route path="/data" element={shell(<DataStudio />)} />
      <Route path="/insights" element={shell(<Insights />)} />
      <Route path="/reports" element={shell(<Reports />)} />
      <Route path="/settings" element={shell(<Settings />)} />
      <Route path="*" element={shell(<Dashboard />)} />
    </Routes>
  );
}
