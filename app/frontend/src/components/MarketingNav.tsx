import { Link } from "react-router-dom";

export function MarketingNav() {
  return (
    <header>
      <div className="marketing-nav">
        <Link className="logo" to="/">
          <div className="logo-symbol"><span>▥</span></div>
          resili<span style={{ color: "#6462dd", marginLeft: -8 }}>plan</span>
        </Link>
        <nav className="nav-links">
          <a href="#top">Home</a>
          <a href="#how-it-works">Our solution</a>
          <a href="#capabilities">Features</a>
          <a href="#faq">Resources</a>
          <Link to="/dashboard">Dashboard</Link>
        </nav>
        <div className="nav-right">
          <Link className="btn mini" to="/scenarios">Scenario lab</Link>
          <Link className="btn primary mini" to="/dashboard">Open workspace ↗</Link>
        </div>
      </div>
    </header>
  );
}
