export const formatNumber = (value: number | undefined): string => {
  if (value === undefined || value === null) {
    return "-";
  }
  return value.toLocaleString();
};

// 金額を億円・兆円でフォーマット
export const formatCurrency = (value: number | undefined, currency: string = 'JPY'): string => {
  if (value === undefined || value === null) {
    return "-";
  }

  const absValue = Math.abs(value);
  
  if (currency === 'USD') {
    // ドル表示
    if (absValue >= 1_000_000_000_000) {
      return `$${(value / 1_000_000_000_000).toFixed(1)}T`;
    } else if (absValue >= 1_000_000_000) {
      return `$${(value / 1_000_000_000).toFixed(1)}B`;
    } else if (absValue >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(1)}M`;
    } else if (absValue >= 1_000) {
      return `$${(value / 1_000).toFixed(1)}K`;
    } else {
      return `$${value.toLocaleString()}`;
    }
  } else {
    // 円表示（億円・兆円）
    if (absValue >= 1_000_000_000_000) {
      return `¥${(value / 1_000_000_000_000).toFixed(1)}兆円`;
    } else if (absValue >= 100_000_000) {
      return `¥${(value / 100_000_000).toFixed(1)}億円`;
    } else if (absValue >= 10_000) {
      return `¥${(value / 10_000).toFixed(1)}万円`;
    } else {
      return `¥${value.toLocaleString()}`;
    }
  }
};

// 財務データ用のフォーマット（データベースの値が円単位の場合）
export const formatFinancialData = (value: number | undefined, currency: string = 'JPY'): string => {
  if (value === undefined || value === null) {
    return "-";
  }

  // データベースの値は既に円単位なので、そのまま使用
  return formatCurrency(value, currency);
};