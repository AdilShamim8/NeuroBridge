"use client";

import { ReactNode, useState } from "react";

type TabGroupProps = {
  items: Array<{ label: string; content: ReactNode }>;
};

export function TabGroup({ items }: TabGroupProps) {
  const [active, setActive] = useState(0);
  return (
    <div className="my-6 rounded-xl border border-black/10 bg-white/90 p-3">
      <div className="mb-2 inline-flex rounded-lg border border-black/10 p-1">
        {items.map((item, index) => (
          <button
            key={item.label}
            onClick={() => setActive(index)}
            className={`rounded-md px-3 py-1 text-xs font-semibold ${active === index ? "bg-brand-ink text-white" : "text-brand-slate"}`}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="text-sm">{items[active]?.content}</div>
    </div>
  );
}
