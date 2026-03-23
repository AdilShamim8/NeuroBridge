import type { MDXComponents } from "mdx/types";

import { ApiEndpoint } from "@/components/mdx/ApiEndpoint";
import { BeforeAfter } from "@/components/mdx/BeforeAfter";
import { Callout } from "@/components/mdx/Callout";
import { CodeBlock } from "@/components/mdx/CodeBlock";
import { ProfileBadge } from "@/components/mdx/ProfileBadge";
import { TabGroup } from "@/components/mdx/TabGroup";

export const mdxComponents: MDXComponents = {
  pre: (props: any) => {
    const child = props.children;
    if (child?.props?.children) {
      return <CodeBlock language={child.props.className?.replace("language-", "") || "text"}>{String(child.props.children)}</CodeBlock>;
    }
    return <pre {...props} />;
  },
  Callout,
  ProfileBadge,
  ApiEndpoint,
  TabGroup,
  BeforeAfter,
  h2: (props: any) => {
    const text = String(props.children ?? "");
    const id = text.toLowerCase().replace(/[^a-z0-9\s-]/g, "").trim().replace(/\s+/g, "-");
    return <h2 id={id} {...props} />;
  },
  h3: (props: any) => {
    const text = String(props.children ?? "");
    const id = text.toLowerCase().replace(/[^a-z0-9\s-]/g, "").trim().replace(/\s+/g, "-");
    return <h3 id={id} {...props} />;
  }
};
