import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";
import terser from "@rollup/plugin-terser";
import typescript from "@rollup/plugin-typescript";

const basePlugins = [
  resolve({ preferBuiltins: false }),
  commonjs(),
  typescript({ tsconfig: "./tsconfig.json" })
];

export default [
  {
    input: "src/index.ts",
    output: {
      file: "dist/esm/index.js",
      format: "esm",
      sourcemap: true
    },
    external: ["fs", "path"],
    plugins: basePlugins
  },
  {
    input: "src/index.ts",
    output: {
      file: "dist/cjs/index.cjs",
      format: "cjs",
      exports: "named",
      sourcemap: true
    },
    external: ["fs", "path"],
    plugins: basePlugins
  },
  {
    // Browser entry excludes NodeFileMemory (fs/path imports break the bundle).
    input: "src/browser.ts",
    output: {
      file: "dist/browser/neurobridge.global.js",
      format: "iife",
      name: "NeuroBridge",
      sourcemap: true
    },
    plugins: [...basePlugins, terser()]
  }
];
