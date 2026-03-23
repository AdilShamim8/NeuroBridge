// @ts-nocheck
import { useMemo, useState } from "react";

import { NeuroBridge, Profile } from "../src/index";

export default function NeuroBridgeDemo() {
  const bridge = useMemo(() => {
    const instance = new NeuroBridge();
    instance.setProfile(Profile.DYSLEXIA);
    return instance;
  }, []);

  const [input, setInput] = useState("Please provide a dense explanation of this architecture.");
  const [output, setOutput] = useState("");

  const adapt = () => {
    const result = bridge.adaptSync(input);
    setOutput(result.adaptedText);
  };

  return (
    <main>
      <h1>NeuroBridge Next.js Example</h1>
      <textarea value={input} onChange={(event) => setInput(event.target.value)} />
      <button onClick={adapt}>Adapt</button>
      <pre>{output}</pre>
    </main>
  );
}
