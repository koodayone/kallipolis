// Root route. Renders the State Atlas directly — it's the doorway into the
// product for both anonymous preview visitors and (eventually) signed-in
// users. The former login-gated cookie-check flow was removed when the
// atlas moved to static export for preview deployment.

import StateAtlas from "@/state-atlas/StateAtlas";

export default function RootPage() {
  return <StateAtlas />;
}
