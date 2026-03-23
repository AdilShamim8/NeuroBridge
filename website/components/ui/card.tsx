import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-black/5 bg-white/90 p-6 shadow-[0_12px_30px_-20px_rgba(20,19,31,0.45)]",
        className
      )}
      {...props}
    />
  );
}
