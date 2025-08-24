declare global {
  interface Window {
    TradingView: {
      widget: new (config: {
        width: string;
        height: string;
        symbol: string;
        interval?: string;
        timezone?: string;
        theme?: "light" | "dark";
        style?: string;
        locale?: string;
        toolbar_bg?: string;
        enable_publishing?: boolean;
        hide_top_toolbar?: boolean;
        hide_legend?: boolean;
        save_image?: boolean;
        container_id: string;
        studies?: string[];
        show_popup_button?: boolean;
        popup_width?: string;
        popup_height?: string;
      }) => any;
    };
  }
}

export {};
