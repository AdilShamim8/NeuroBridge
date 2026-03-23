"use client";

import { useEffect, useState } from "react";

type AnimatedCounterProps = {
  target: number;
};

export function AnimatedCounter({ target }: AnimatedCounterProps) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    let frame = 0;
    const duration = 1200;
    const start = performance.now();

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.floor(target * eased));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  return <>{value.toLocaleString()}+</>;
}
