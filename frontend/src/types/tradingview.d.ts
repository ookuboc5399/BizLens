declare global {
  interface Window {
    TradingView: {
      MediumWidget: new (config: {
        container_id: string;
        symbols: string[][];
        chartOnly?: boolean;
        width: string;
        height: string;
        locale: string;
        colorTheme: "light" | "dark";
        gridLineColor?: string;
        trendLineColor?: string;
        fontColor?: string;
        underLineColor?: string;
        isTransparent?: boolean;
        autosize?: boolean;
        container: string;
        showFloatingTooltip?: boolean;
      }) => any;
    };
  }
}

export {};
