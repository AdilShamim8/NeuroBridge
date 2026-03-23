import { Card } from "@/components/ui/card";

const cards = [
  { name: "ADHD", detail: "Summary-first structure, chunked reading, and clearer prioritization." },
  { name: "Autism", detail: "Reduced idioms and ambiguity with explicit, direct wording." },
  { name: "Dyslexia", detail: "Shorter sentences, cleaner spacing, and better scan patterns." },
  { name: "Anxiety", detail: "Urgency softening and calm framing while preserving intent." },
  { name: "Dyscalculia", detail: "Number context and relatable comparisons for magnitude." }
];

export function ProfileCards() {
  return (
    <section className="mt-16">
      <h2 className="text-3xl font-black text-brand-ink">Five adaptive profiles</h2>
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {cards.map((card) => (
          <Card key={card.name} className="p-4">
            <p className="text-sm font-black text-brand-primary">{card.name}</p>
            <p className="mt-2 text-sm text-brand-slate">{card.detail}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
