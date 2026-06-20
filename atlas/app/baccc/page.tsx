"use client";

import { useEffect } from "react";

// /baccc is the consortium entry — redirect to /baccc-adm (the canonical
// Advanced Manufacturing sector view), mirroring /smccd → /smccd-adm.
export default function BacccRedirect() {
  useEffect(() => { window.location.replace("/baccc-adm"); }, []);
  return null;
}
