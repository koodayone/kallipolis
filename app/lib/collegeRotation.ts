/**
 * Shared college rotation order for the landing page.
 * Both AtlasPreview and StateAtlas cycle through this list in sync.
 */

export const ROTATION_COLLEGES = [
  { id: "shasta",    name: "Shasta College",                 district: "Shasta-Tehama-Trinity JCCD", neonColor: 0x2bee64, neonHex: "#2bee64" },
  { id: "lassen",    name: "Lassen College",                 district: "Lassen CCD",                 neonColor: 0xf07c42, neonHex: "#f07c42" },
  { id: "laketahoe", name: "Lake Tahoe Community College",   district: "Lake Tahoe CCD",             neonColor: 0x4fd1fd, neonHex: "#4fd1fd" },
  { id: "foothill",  name: "Foothill College",               district: "Foothill-De Anza CCD",       neonColor: 0xf0425e, neonHex: "#f0425e" },
  { id: "sequoias",  name: "College of the Sequoias",        district: "Sequoias CCD",               neonColor: 0xb9ff1a, neonHex: "#b9ff1a" },
  { id: "compton",   name: "Compton College",                district: "Compton CCD",                neonColor: 0xf04283, neonHex: "#f04283" },
  { id: "desert",    name: "College of the Desert",          district: "Desert CCD",                 neonColor: 0xffc933, neonHex: "#ffc933" },
] as const;

export const CYCLE_INTERVAL = 5000;
export const FADE_DURATION = 700;
