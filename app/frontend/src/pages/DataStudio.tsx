import { useState } from "react";
import { Link } from "react-router-dom";
import { api, type DataSummary, type TablePreview } from "../lib/api";
import { useApi } from "../lib/useApi";
import { Gate } from "../components/States";
import { PageHead, AssumptionsBanner } from "../components/Layout";
import { fmt } from "../lib/format";

function DatasetPreview({ tables }: { tables: string[] }) {
  const [table, setTable] = useState(tables.includes("products") ? "products" : tables[0]);
  const prev = useApi<TablePreview>(() => api.dataPreview(table, 8), [table]);
  return (
    <div className="card">
      <div className="card-header">
        <div><div className="card-title">Dataset preview</div><div className="card-sub">See the actual rows of any source table</div></div>
        <select className="filter-chip" value={table} onChange={(e) => setTable(e.target.value)} aria-label="Choose a table">
          {tables.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
      <Gate r={prev} skeletonH={160}>
        {(p) => (
          <>
            <div className="table-wrap"><table className="data-table">
              <thead><tr>{p.columns.map((c) => <th key={c}>{c}</th>)}</tr></thead>
              <tbody>{p.rows.map((row, i) => (
                <tr key={i}>{row.map((v, j) => <td key={j}>{v === null ? "—" : String(v)}</td>)}</tr>
              ))}</tbody>
            </table></div>
            <div className="tiny muted" style={{ marginTop: 10 }}>Showing first {p.preview_rows} of {fmt(p.total_rows)} rows · cleaned table <b>{p.table}.v1.csv</b></div>
          </>
        )}
      </Gate>
    </div>
  );
}

export default function DataStudio() {
  const sum = useApi<DataSummary>(() => api.dataSummary(), []);
  return (
    <>
      <PageHead eyebrow="Dataset overview" title="See the data behind every decision."
        sub="Inspect the validated source tables, data-quality checks and sample records."
        actions={<Link to="/network" className="btn dark">Inspect network →</Link>} />
      <AssumptionsBanner>The dataset is real and validated; cost parameters (used later) are assumed and documented separately.</AssumptionsBanner>

      <Gate r={sum} skeletonH={120}>
        {(d) => {
          const v = d.validation as any;
          const checks: [string, boolean][] = [
            ["Audited counts reproduce", !!v.counts_all_match],
            ["No referential-integrity failures", Array.isArray(v.referential_failures) && v.referential_failures.length === 0],
            ["No duplicate keys", Array.isArray(v.duplicate_key_sheets) && v.duplicate_key_sheets.length === 0],
            ["BOM is acyclic (DAG)", !!v.bom_is_dag],
            ["No negative quantities", v.any_negative_quantities === false],
            ["No missing values", v.columns_with_missing === 0],
          ];
          return (
            <>
              <div className="stat-grid">
                {[["Source workbook", d.source_format, "original format"],
                  ["Worksheets", `${d.worksheets}`, "source tables"],
                  ["Demand horizon", "14 periods", d.horizon],
                  ["Pipeline", "Validated", "cleaned & loaded"]].map((x, i) => (
                  <div className="stat-card" key={i}><div className="stat-top">{x[0]}<span>▣</span></div>
                    <div className="stat-value" style={{ fontSize: (x[1] as string).length > 7 ? 21 : 28 }}>{x[1]}</div><div className="tiny muted">{x[2]}</div></div>
                ))}
              </div>

              <DatasetPreview tables={d.tables.map((t) => t.table)} />

              <div className="grid-2-even">
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Import your own data</div><div className="card-sub">Live upload status</div></div><span className="pill amber">Not enabled</span></div>
                  <div className="upload-zone" style={{ opacity: 0.75 }}>
                    <span className="upload-icon">↥</span>
                    <h3>Server-side ingestion</h3>
                    <p>This build optimizes against the bundled, validated dataset. Live XLSB/CSV upload and re-validation are a planned extension — so no file is accepted here rather than faking a successful import.</p>
                  </div>
                  <div className="notice" style={{ marginTop: 14 }}>Source: <b>{d.source_file}</b> · {d.status}</div>
                </div>
                <div className="card">
                  <div className="card-header"><div><div className="card-title">Data quality framework</div><div className="card-sub">Validation checks (real results)</div></div></div>
                  {checks.map(([label, ok], i) => (
                    <div className="flow-item" key={i}><span><b>{label}</b></span><span className={`small-tag ${ok ? "" : "red"}`}>{ok ? "Pass" : "Review"}</span></div>
                  ))}
                  <div className="tiny muted" style={{ marginTop: 10 }}>BOM identity rows isolated: {fmt(v.bom_identity_rows)} (benign mother==child).</div>
                </div>
              </div>

              <div className="card">
                <div className="card-header"><div><div className="card-title">Source table catalog</div><div className="card-sub">The validated relational schema</div></div><span className="pill">{d.worksheets} worksheets</span></div>
                <div className="table-wrap"><table className="data-table">
                  <thead><tr><th>Table</th><th>Rows</th><th>Description</th><th>Role</th></tr></thead>
                  <tbody>{d.tables.map((t) => (
                    <tr key={t.table}><td><b>{t.table}</b></td><td>{t.rows === null ? "—" : fmt(t.rows)}</td><td>{t.description}</td>
                      <td><span className="small-tag blue">{t.role}</span></td></tr>
                  ))}</tbody>
                </table></div>
              </div>
            </>
          );
        }}
      </Gate>
    </>
  );
}
