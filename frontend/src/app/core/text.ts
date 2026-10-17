/** Une elementos al estilo español: «A, B y C». */
export function joinEs(items: string[]): string {
  if (items.length <= 1) return items.join('');
  return `${items.slice(0, -1).join(', ')} y ${items[items.length - 1]}`;
}

export const capitalize = (text: string): string => text.charAt(0).toUpperCase() + text.slice(1);

export const lowerFirst = (text: string): string => text.charAt(0).toLowerCase() + text.slice(1);
