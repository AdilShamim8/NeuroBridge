import { NewsletterForm } from "@/components/NewsletterForm";

export default function NewsletterPage() {
  return (
    <section className="space-y-5">
      <h1 className="text-4xl font-black text-brand-ink">Newsletter</h1>
      <p className="max-w-2xl text-brand-slate">
        Product updates, accessibility notes, and release previews. Double opt-in confirmation is required.
      </p>
      <div className="rounded-2xl border border-black/10 bg-white/85 p-6">
        <NewsletterForm />
        <p className="mt-3 text-xs text-brand-slate">
          First email: Welcome to NeuroBridge - here's what's coming in v0.2.0
        </p>
      </div>
    </section>
  );
}
