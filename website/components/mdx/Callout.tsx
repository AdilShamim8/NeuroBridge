import { AlertCircle, AlertTriangle, Info, Lightbulb } from "lucide-react";
import { ReactNode } from "react";

type CalloutType = "info" | "warning" | "tip" | "danger";

type CalloutProps = {
  type?: CalloutType;
  title?: string;
  children: ReactNode;
};

const STYLE: Record<CalloutType, string> = {
  info: "border-sky-200 bg-sky-50 text-sky-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  tip: "border-emerald-200 bg-emerald-50 text-emerald-900",
  danger: "border-rose-200 bg-rose-50 text-rose-900"
};

const ICON = {
  info: Info,
  warning: AlertTriangle,
  tip: Lightbulb,
  danger: AlertCircle
};

export function Callout({ type = "info", title, children }: CalloutProps) {
  const Icon = ICON[type];
  return (
    <div className={`my-6 rounded-xl border p-4 ${STYLE[type]}`}>
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-5 w-5" />
        <div>
          {title ? <p className="mb-1 font-bold">{title}</p> : null}
          <div className="text-sm leading-7">{children}</div>
        </div>
      </div>
    </div>
  );
}
