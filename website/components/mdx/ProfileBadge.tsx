type ProfileBadgeProps = {
  profile: "adhd" | "autism" | "dyslexia" | "anxiety" | "dyscalculia";
};

const STYLE: Record<ProfileBadgeProps["profile"], string> = {
  adhd: "bg-indigo-100 text-indigo-800",
  autism: "bg-cyan-100 text-cyan-800",
  dyslexia: "bg-fuchsia-100 text-fuchsia-800",
  anxiety: "bg-emerald-100 text-emerald-800",
  dyscalculia: "bg-orange-100 text-orange-800"
};

export function ProfileBadge({ profile }: ProfileBadgeProps) {
  return <span className={`badge-pill capitalize ${STYLE[profile]}`}>{profile}</span>;
}
