import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "badge-pill inline-flex items-center border border-brand-primary/25 bg-brand-mist text-brand-ink",
        className
      )}
      {...props}
    />
  );
}
