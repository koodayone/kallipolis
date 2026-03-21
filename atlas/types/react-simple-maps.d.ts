declare module "react-simple-maps" {
  import { ComponentType, ReactNode, SVGProps, MouseEventHandler } from "react";

  interface ProjectionConfig {
    center?: [number, number];
    scale?: number;
    rotate?: [number, number, number];
  }

  interface ComposableMapProps {
    projection?: string;
    projectionConfig?: ProjectionConfig;
    width?: number;
    height?: number;
    style?: React.CSSProperties;
    children?: ReactNode;
  }

  interface GeographiesProps {
    geography: string | object;
    children: (props: { geographies: GeoFeature[] }) => ReactNode;
  }

  interface GeoFeature {
    rsmKey: string;
    properties: Record<string, string | number>;
    type: string;
    geometry: object;
  }

  interface GeographyProps extends SVGProps<SVGPathElement> {
    geography: GeoFeature;
    fill?: string;
    stroke?: string;
    strokeWidth?: number;
    cursor?: string;
    onMouseEnter?: MouseEventHandler<SVGPathElement>;
    onMouseLeave?: MouseEventHandler<SVGPathElement>;
    onClick?: MouseEventHandler<SVGPathElement>;
    style?: {
      default?: React.CSSProperties;
      hover?: React.CSSProperties;
      pressed?: React.CSSProperties;
    };
  }

  interface MarkerProps {
    coordinates: [number, number];
    children?: ReactNode;
    onClick?: MouseEventHandler<SVGGElement>;
    onMouseEnter?: MouseEventHandler<SVGGElement>;
    onMouseLeave?: MouseEventHandler<SVGGElement>;
  }

  export const ComposableMap: ComponentType<ComposableMapProps>;
  export const Geographies: ComponentType<GeographiesProps>;
  export const Geography: ComponentType<GeographyProps>;
  export const Marker: ComponentType<MarkerProps>;
  export const ZoomableGroup: ComponentType<{
    center?: [number, number];
    zoom?: number;
    children?: ReactNode;
  }>;
}
