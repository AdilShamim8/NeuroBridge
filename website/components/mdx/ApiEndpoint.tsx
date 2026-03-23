type ApiEndpointProps = {
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  path: string;
  description: string;
};

export function ApiEndpoint({ method, path, description }: ApiEndpointProps) {
  return (
    <div className="my-6 rounded-xl border border-black/10 bg-white p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="badge-pill bg-brand-ink text-white">{method}</span>
        <code className="rounded bg-brand-mist px-2 py-1 font-mono text-xs text-brand-ink">{path}</code>
      </div>
      <p className="mt-2 text-sm text-brand-slate">{description}</p>
    </div>
  );
}
