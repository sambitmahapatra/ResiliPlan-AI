// Display formatting. Monetary unit is "MU" (dimensionless, ASSUMED) — never a real currency.
export const fmt = (n: number | null | undefined, dec = 0): string =>
  n === null || n === undefined || Number.isNaN(n)
    ? "—"
    : Number(n).toLocaleString("en-US", { maximumFractionDigits: dec, minimumFractionDigits: dec });

export const mu = (n: number | null | undefined): string =>
  n === null || n === undefined ? "—" : `${fmt(n)} MU`;

export const pct = (n: number | null | undefined, dec = 1): string =>
  n === null || n === undefined ? "—" : `${fmt(n, dec)}%`;

export const titleCase = (s: string): string => s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export const HORIZON = "Periods 61–74";
