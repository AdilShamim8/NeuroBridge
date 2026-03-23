# Day 25 - Hacker News Launch

## Show HN Title

Show HN: NeuroBridge - open-source middleware to adapt AI output for ADHD, autism, dyslexia

## First Comment (post immediately after submission)

I built NeuroBridge because I kept seeing the same failure mode in AI products: answers were factually good but cognitively hostile for many users. Long, linear, urgency-heavy prose works for some people and blocks others.

NeuroBridge is a middleware layer, not a model replacement. You keep your current LLM stack and run responses through a profile-aware transform pipeline (chunking, tone/urgency rewrite, ambiguity cleanup, number contextualization, priority reordering). It supports explicit profiles today (ADHD, autism, dyslexia, anxiety, dyscalculia), with optional feedback-informed tuning.

Three likely objections:

1) "Why not just prompt the LLM?"
Prompting helps, but prompt-only adaptation is inconsistent across model vendors, model updates, and prompt templates. Middleware gives one policy surface you can test, version, and enforce across routes. It also avoids adding prompt bloat latency for every request.

2) "How is this different from changing the system prompt?"
System prompts are static instruction text. NeuroBridge adds profile configs, deterministic transform stages, output adapters (markdown/html/plain/json/tts), and memory-backed tuning signals. That gives repeatable behavior and better operational control.

3) "Is this clinically validated?"
Not as a medical device, and I want to be explicit about that. It is research-informed and community-informed engineering, not diagnosis or treatment. The goal is practical cognitive accessibility improvements in real software workflows, with transparent limitations.

I would value technical critique on evaluation design, failure modes, and where adaptation can accidentally reduce clarity. Repo: https://github.com/yourusername/neurobridge
