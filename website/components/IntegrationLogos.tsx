import { Badge } from "@/components/ui/badge";

const integrations = ["OpenAI", "Anthropic", "LangChain", "HuggingFace"];

export function IntegrationLogos() {
  return (
    <section className="mt-16 rounded-2xl border border-black/10 bg-white/80 p-6">
      <p className="text-sm font-bold uppercase tracking-wide text-brand-slate">Integrations</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {integrations.map((item) => (
          <Badge key={item}>{item}</Badge>
        ))}
      </div>
    </section>
  );
}
