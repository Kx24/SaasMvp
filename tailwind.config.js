/**
 * Config compartida por TODOS los temas (sistema de diseño, #AUD-11/#TOOL-04).
 *
 * Los colores NO son hex fijos -- apuntan a las variables CSS que cada
 * base.html define en su propio bloque `:root`, templadas desde
 * ClientSettings. Un solo compilado (static/css/output.css) sirve a los
 * 3 tenants reales; el color real lo resuelve el navegador según qué
 * :root cargó esa página. Antes cada tema repetía su propio
 * tailwind.config con hex hardcodeado Y su propio bloque :root con el
 * mismo valor otra vez, sin relación entre ambos -- dos fuentes de
 * verdad para el mismo dato (ver informe "Tailwind, hoy").
 *
 * `body`/`sans` conviven como alias del mismo token: `andesscale` ya
 * usaba `font-body` en vez de `font-sans` antes de esta migración: se
 * deja el alias para no forzar un rename de clases en sus templates,
 * pero `sans` es el nombre preferido para temas nuevos (ver
 * docs/design-system.md).
 *
 * Nota: la paleta fija de Rancho Cachimba (dorado/claro/tierra/carbon,
 * definida en su :root) no se agrega acá -- se confirmó que ningún
 * template la usa como clase Tailwind (`bg-dorado`, etc.), solo como
 * `var(--amarillo-dorado)` en estilos inline. Config de Tailwind muerta,
 * no se migra.
 */
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        accent: 'var(--color-accent)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        body: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
