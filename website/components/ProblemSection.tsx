import { Card } from "@/components/ui/card";

const examples = [
  {
    profile: "ADHD",
    before: "The process includes multiple optional paths and context-sensitive dependencies that might matter later.",
    after: "Bottom line first: start with one path, then review dependencies in short steps."
  },
  {
    profile: "Autism",
    before: "We should circle back soon and move the needle.",
    after: "We will revisit this tomorrow and improve the result by 10%."
  },
  {
    profile: "Dyslexia",
    before: "This sentence is overloaded with clauses, commas, and abstract qualifiers that make it hard to parse.",
    after: "This is easier to read. One idea per sentence."
  },
  {
    profile: "Anxiety",
    before: "Urgent. Critical. Fix this now or everything fails.",
    after: "This is important. Please review when ready."
  },
  {
    profile: "Dyscalculia",
    before: "Completion increased by 37% and budget impact is $420,000.",
    after: "Completion increased by 37% (about 1 in 3). Budget impact is $420,000 (around a house deposit scale)."
  }
];

export function ProblemSection() {
  return (
    <section className="mt-16">
      <h2 className="text-3xl font-black text-brand-ink">The accessibility gap in AI output</h2>
      <p className="mt-2 max-w-2xl text-brand-slate">One model response can be clear for one brain and exhausting for another.</p>
      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {examples.map((item) => (
          <Card key={item.profile} className="space-y-3">
            <p className="text-xs font-bold uppercase tracking-wide text-brand-secondary">{item.profile}</p>
            <p className="rounded-lg bg-rose-50 p-3 text-sm text-brand-ink"><strong>Before:</strong> {item.before}</p>
            <p className="rounded-lg bg-emerald-50 p-3 text-sm text-brand-ink"><strong>After:</strong> {item.after}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
