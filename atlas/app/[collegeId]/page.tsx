"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { ALL_FORM_KEYS, FORM_NAMES, FORM_URL_SLUGS } from "@/college-atlas/scene";
import { useHomeSceneContext } from "@/college-atlas/homeSceneContext";
import { getCollegeAtlasConfig } from "@/config/collegeAtlasConfigs";
import AtlasMenu from "@/auth/AtlasMenu";
import KallipolisBrand from "@/ui/KallipolisBrand";
import AtlasHeader from "@/ui/AtlasHeader";

export default function CollegeAtlasHomePage() {
  const { collegeId } = useParams<{ collegeId: string }>();
  const config = getCollegeAtlasConfig(collegeId);
  const { projectedPositions, hoveredForm, setHoveredForm } = useHomeSceneContext();

  if (!config) return null;

  return (
    <>
      {/* Home header — brand on the left, college name centered, State Atlas menu on the right */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.35 }}
        style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 6 }}
      >
        <AtlasHeader
          position="static"
          title={config.name}
          leftSlot={<KallipolisBrand />}
          rightSlot={
            <AtlasMenu navItems={[{ label: "State Atlas", href: "/state", icon: (
              <svg width="12" height="16" viewBox="0 0 16 22" fill="#c9a84c">
                <path d="M0.0,3.6L0.9,5.0L1.1,7.2L2.5,9.1L2.2,8.7L2.2,9.3L3.0,9.7L3.1,9.0L4.6,9.2L3.2,9.3L3.9,10.6L3.1,9.7L2.9,10.4L3.2,11.3L4.2,12.0L3.8,12.6L3.9,13.2L5.9,16.0L5.9,17.3L9.2,18.5L9.3,19.2L10.8,20.2L11.3,22.0L15.4,21.5L15.1,20.0L15.5,18.4L16.0,18.0L15.2,16.3L6.9,7.0L6.9,0.0L0.3,0.0L0.5,1.3L0.3,2.9L0.5,2.7L0.0,3.6Z" />
              </svg>
            ) }]} />
          }
        />
      </motion.div>

      {/* Form labels — projected from the 3D scene, each is a link into its form route */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.35 }}
        style={{ position: "fixed", inset: 0, zIndex: 5, pointerEvents: "none" }}
      >
        {ALL_FORM_KEYS.map((key) => {
          const pos = projectedPositions[key];
          if (!pos) return null;
          const isHovered = hoveredForm === key;
          return (
            <Link
              key={key}
              href={`/${collegeId}/${FORM_URL_SLUGS[key]}`}
              onMouseEnter={() => setHoveredForm(key)}
              onMouseLeave={() => setHoveredForm(null)}
              style={{
                position: "absolute",
                top: `${pos.y + 14}%`,
                left: `${pos.x}%`,
                transform: "translateX(-50%)",
                pointerEvents: "auto",
                fontFamily: "var(--font-inter), Inter, system-ui, sans-serif",
                fontSize: "13px",
                fontWeight: 600,
                letterSpacing: "0.13em",
                textTransform: "uppercase",
                color: isHovered ? "#c9a84c" : "rgba(255,255,255,0.35)",
                whiteSpace: "nowrap",
                textDecoration: "none",
                transition: "color 0.3s ease-in-out",
              }}
            >
              {FORM_NAMES[key]}
            </Link>
          );
        })}
      </motion.div>
    </>
  );
}
