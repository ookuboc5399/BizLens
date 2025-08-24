declare module 'react-heatmap-grid' {
  interface HeatMapProps {
    xLabels: string[];
    yLabels: string[];
    data: number[][];
    xLabelsLocation?: 'top' | 'bottom';
    squares?: boolean;
    height?: number;
    onClick?: (x: number, y: number) => void;
    cellStyle?: (
      background: string,
      value: number,
      min: number,
      max: number
    ) => React.CSSProperties;
    cellRender?: (value: number) => React.ReactNode;
  }

  const HeatMap: React.FC<HeatMapProps>;
  export default HeatMap;
}
