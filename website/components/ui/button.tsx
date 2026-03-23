import { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  children: ReactNode;
};

export function Button({ className, variant = "primary", children, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-12 items-center justify-center rounded-xl px-4 py-2 text-base font-semibold transition",
        variant === "primary" &&
          "bg-brand-primary text-white shadow-halo hover:-translate-y-0.5 hover:brightness-105",
        variant === "secondary" && "bg-brand-secondary text-white hover:brightness-105",
        variant === "ghost" && "bg-transparent text-brand-ink hover:bg-black/5",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
