import { Table, ArrowUpDown, ChevronDown } from 'lucide-react';
import { useState } from 'react';

interface Props {
  data: {
    headers?: string[];
    rows?: string[][];
  };
  title?: string;
}

export function DataTableView({ data, title }: Props) {
  const headers = data.headers || [];
  const rows = data.rows || [];
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const sortedRows = sortCol !== null
    ? [...rows].sort((a, b) => {
        const va = a[sortCol] || '';
        const vb = b[sortCol] || '';
        const cmp = va.localeCompare(vb, undefined, { numeric: true });
        return sortDir === 'asc' ? cmp : -cmp;
      })
    : rows;

  const toggleSort = (col: number) => {
    if (sortCol === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortCol(col);
      setSortDir('asc');
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-white/5">
        <Table size={20} className="text-aria-400" />
        <h2 className="text-lg font-semibold text-white/90">{title || 'Data'}</h2>
        <span className="text-xs text-white/30 ml-auto">{rows.length} rows</span>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {headers.length > 0 ? (
          <table className="w-full">
            <thead className="sticky top-0 bg-[var(--bg-secondary)]">
              <tr>
                {headers.map((h, i) => (
                  <th
                    key={i}
                    onClick={() => toggleSort(i)}
                    className="text-left px-4 py-3 text-xs text-white/40 uppercase tracking-wider 
                               border-b border-white/5 cursor-pointer hover:text-white/60 transition-colors select-none"
                  >
                    <div className="flex items-center gap-1">
                      {h}
                      <ArrowUpDown size={10} className={sortCol === i ? 'text-aria-400' : 'text-white/15'} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, ri) => (
                <tr
                  key={ri}
                  className="hover:bg-white/[0.03] transition-colors border-b border-white/[0.03]"
                >
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-4 py-3 text-sm text-white/70">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-12 text-white/20">
            <Table size={40} className="mx-auto mb-3" />
            <p>No table data to display</p>
          </div>
        )}
      </div>
    </div>
  );
}
