import { useState, useEffect } from "react";

const SENSORS = [
  "T24", "T30", "T50", "P15", "P30", "Nf", "Nc",
  "Ps30", "phi", "NRf", "NRc", "BPR", "W31", "W32", "htBleed",
];

export default function CustomInputTable({
  cycles,
  onChange,
  assetId,
  onAssetIdChange,
}) {
  const [rows, setRows] = useState(cycles);

  useEffect(() => {
    if (cycles.length !== rows.length) {
      setRows(cycles);
    }
  }, [cycles, rows.length]);

  const handleCellChange = (rowIdx, field, value) => {
    const num = value === "" ? "" : parseFloat(value);

    setRows((prev) => {
      const next = [...prev];
      next[rowIdx] = { ...next[rowIdx], [field]: num };
      onChange?.(next);
      return next;
    });
  };

  const handleAssetIdChange = (e) => {
    onAssetIdChange?.(e.target.value);
  };

  return (
    <>
      <div
        className="form-row"
        style={{ gridTemplateColumns: "1fr 1fr", marginBottom: 16 }}
      >
        <div className="field">
          <label>Asset ID</label>
          <input
            type="text"
            value={assetId}
            onChange={handleAssetIdChange}
            placeholder="CUSTOM-001"
            maxLength={64}
          />
        </div>
      </div>

      <div className="custom-table-wrap">
        <table>
          <thead>
            <tr>
              <th style={{ width: "60px", minWidth: "60px" }}>Cycle</th>

              {SENSORS.map((s) => (
                <th
                  key={s}
                  style={{ width: "90px", minWidth: "90px" }}
                >
                  {s}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                <td>
                  <input
                    type="number"
                    value={row.cycle ?? i + 1}
                    onChange={(e) =>
                      handleCellChange(
                        i,
                        "cycle",
                        parseInt(e.target.value) || ""
                      )
                    }
                    min="1"
                    step="1"
                    style={{ width: "60px" }}
                  />
                </td>

                {SENSORS.map((s) => (
                  <td key={s}>
                    <input
                      type="number"
                      value={row[s] ?? ""}
                      onChange={(e) =>
                        handleCellChange(i, s, e.target.value)
                      }
                      step="any"
                      placeholder="—"
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}