import { ImageResponse } from "@vercel/og";

export const runtime = "edge";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const profile = searchParams.get("profile") || "NeuroBridge";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          background: "linear-gradient(135deg, #f3f1ff 0%, #eefcf7 100%)",
          color: "#14131f",
          padding: 64,
          flexDirection: "column",
          justifyContent: "center"
        }}
      >
        <div style={{ fontSize: 34, color: "#5b5c70", marginBottom: 14 }}>NeuroBridge</div>
        <div style={{ fontSize: 72, fontWeight: 800, marginBottom: 12 }}>AI That Speaks Your Language</div>
        <div style={{ fontSize: 38, color: "#7F77DD" }}>Profile: {profile}</div>
      </div>
    ),
    {
      width: 1200,
      height: 630
    }
  );
}
