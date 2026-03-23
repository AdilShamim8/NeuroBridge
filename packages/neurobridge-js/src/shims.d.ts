declare module "sentence-splitter" {
  export function split(input: string): Array<{ type?: string; raw?: string }>;
}

declare module "fs" {
  export function mkdirSync(path: string, options?: { recursive?: boolean }): void;
  export function readFileSync(path: string, encoding: "utf-8"): string;
  export function writeFileSync(path: string, content: string, encoding: "utf-8"): void;
}

declare module "path" {
  export function dirname(path: string): string;
}
