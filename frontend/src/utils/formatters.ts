export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('ja-JP').format(num);
}; 