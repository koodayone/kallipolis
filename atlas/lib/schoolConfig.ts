export type SchoolConfig = {
  name: string;
  logoPath: string;
  brandColor: string;
  brandColorDim: string; // light tint for badge backgrounds
};

export const schoolConfig: SchoolConfig = {
  name: "Foothill College",
  logoPath: "/foothill-logo-2.png",
  brandColor: "#7B2D3E",
  brandColorDim: "#f5eaed",
};
