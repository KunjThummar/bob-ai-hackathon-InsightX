import {
  BarChart, Bar, Cell, XAxis, YAxis, Tooltip,
  CartesianGrid, ResponsiveContainer,
} from "recharts";

const CHART_COLORS = {
  READY:    "#34D399",
  CAUTION:  "#FBBF24",
  CRITICAL: "#F87171",
};

const LEGEND_COLORS = {
  READY:    "#059669",
  CAUTION:  "#D97706",
  CRITICAL: "#DC2626",
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "rgba(255,255,255,0.92)",
      border: "1px solid rgba(180,200,220,0.5)",
      borderRadius: 8,
      padding: "8px 14px",
      boxShadow: "0 4px 16px rgba(16,24,40,0.10)",
      fontSize: 12.5,
      fontFamily: "Inter, sans-serif",
    }}>
      <strong>{label}</strong>: {payload[0].value} assets
    </div>
  );
};

export default function ReadinessCard({ assets }) {
  const counts = { READY: 0, CAUTION: 0, CRITICAL: 0 };
  assets.forEach((a) => {
    if (counts[a.status] !== undefined) counts[a.status]++;
  });

  const data = [
    { status: "READY",    count: counts.READY,    color: CHART_COLORS.READY },
    { status: "CAUTION",  count: counts.CAUTION,  color: CHART_COLORS.CAUTION },
    { status: "CRITICAL", count: counts.CRITICAL, color: CHART_COLORS.CRITICAL },
  ];

  return (
    <div className="card" style={{ minWidth: 280 }}>
      <div className="card-title">Readiness Distribution</div>
      <div style={{ height: 210 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 6, right: 24, left: 8, bottom: 6 }}
          >
            <CartesianGrid
              horizontal={false}
              strokeDasharray="3 3"
              stroke="rgba(0,0,0,0.06)"
            />
            <XAxis
              type="number"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11, fill: "#6B7280", fontFamily: "Inter, sans-serif" }}
            />
            <YAxis
              dataKey="status"
              type="category"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 12, fill: "#1F2937", fontFamily: "Inter, sans-serif", fontWeight: 500 }}
              width={72}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(29,78,216,0.04)" }} />
            <Bar dataKey="count" radius={[0, 6, 6, 0]} isAnimationActive={true} animationDuration={700}>
              {data.map((entry) => (
                <Cell key={entry.status} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "flex", gap: 14, marginTop: 10, fontSize: 12, color: "#6B7280" }}>
        {data.map((d) => (
          <span key={d.status} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              width: 10,
              height: 10,
              borderRadius: 3,
              background: LEGEND_COLORS[d.status],
              flexShrink: 0,
            }} />
            <span style={{ fontWeight: 500, color: "#1F2937" }}>{d.status}:</span> {d.count}
          </span>
        ))}
      </div>
    </div>
  );
}