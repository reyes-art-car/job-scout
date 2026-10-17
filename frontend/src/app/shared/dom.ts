/** Lectura tipada del valor de un evento de formulario (evita `$any` en las plantillas). */
export const inputValue = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value;

export const inputChecked = (event: Event): boolean => (event.target as HTMLInputElement).checked;
