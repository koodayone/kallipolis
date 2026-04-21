"use client";

import RisingSun from "@/ui/RisingSun";

type Props = {
  formName: string;
};

export default function FormHeader({ formName }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px", paddingTop: "40px" }}>
      <RisingSun style={{ width: "90px", height: "auto" }} />
      <div style={{ textAlign: "center" }}>
        <h1
          className="text-[24px] md:text-[30px] leading-[1.12]"
          style={{ fontFamily: "var(--font-days-one), sans-serif", fontWeight: 400, fontStyle: "italic", textTransform: "uppercase", letterSpacing: "0.1em", color: "#ffffff", margin: 0 }}
        >
          {formName}
        </h1>
        <div style={{ width: 64, height: 2, background: "#c9a84c", borderRadius: 1, opacity: 0.9, margin: "12px auto 0" }} />
      </div>
    </div>
  );
}
