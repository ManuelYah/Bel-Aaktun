/**
 * URL base de la API.
 * - Con `ng serve` (puerto 4200) se usa el backend en localhost:5000.
 * - En cualquier otro caso (nginx en el servidor) se usa la ruta relativa /api,
 *   que nginx reenvía al backend. Así no hay que recompilar según el dominio.
 */
const enDesarrollo =
  typeof location !== 'undefined' && location.port === '4200';

export const API_URL = enDesarrollo ? 'http://localhost:5000/api' : '/api';

/** ¿Esta URL es de nuestra API? (para que el interceptor adjunte el token) */
export function esUrlDeLaApi(url: string): boolean {
  return (
    url.startsWith('/api/') ||
    /^https?:\/\/(localhost|127\.0\.0\.1):5000\//.test(url)
  );
}
