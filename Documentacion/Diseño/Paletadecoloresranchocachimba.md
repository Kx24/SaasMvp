# Guía de Estilo y Paleta de Colores: Rancho Interactivo CACHIMBA Maullín

**Ubicación del Documento:** `docs/design/paleta_rancho_cachimba.md`  
**Propósito:** Definición de tokens de diseño, paleta de colores y reglas de UI/UX para el sitio web, redes sociales y piezas de comunicación de Rancho Cachimba[cite: 3].  
**Combinación Base de Identidad:** `#064B20` + `#FFD500` + `#FFFFFF`[cite: 3].

---

## 1. Paleta Principal de Colores

Inspirada directamente en el imagotipo oficial (verdes profundos para naturaleza/territorio, amarillos para energía/diversión y neutros para legibilidad)[cite: 3].

| Nombre del Color | Código HEX | Rol y Uso en la Interfaz |
| :--- | :--- | :--- |
| **Verde Rancho** | `#064B20` | Color principal de fondos, encabezados, navegación, footer y botones secundarios[cite: 3]. |
| **Verde Bosque** | `#0B642B` | Estado `:hover`, secciones secundarias y tarjetas[cite: 3]. |
| **Amarillo Cachimba** | `#FFD500` | CTA principal (Llamados a la acción) y acentos destacados[cite: 3]. |
| **Amarillo Dorado** | `#EFB900` | Estado `:hover` de CTAs, bordes y detalles[cite: 3]. |
| **Blanco** | `#FFFFFF` | Fondos de la página y textos sobre fondos oscuros/verdes[cite: 3]. |
| **Verde Muy Claro** | `#EAF4EC` | Fondos suaves de tarjetas y contenedores de información[cite: 3]. |
| **Tierra** | `#6B4F32` | Detalles naturales, madera y recursos secundarios[cite: 3]. |
| **Carbón** | `#172019` | Texto principal, párrafos y títulos para máxima legibilidad[cite: 3]. |

---

## 2. Reglas de Aplicación Web (UI/UX Design)

### Proporción y Distribución
* **Base Visual:** Verde Rancho (`#064B20`) y Blanco (`#FFFFFF`)[cite: 3].
* **Color de Acción (CTA):** Amarillo Cachimba (`#FFD500`)[cite: 3].
* **Soporte / Tarjetas:** Verde Muy Claro (`#EAF4EC`) y Tierra (`#6B4F32`)[cite: 3].

### Mapeo de Elementos de Interfaz
* **Navegación / Header / Footer:** Fondo Verde Rancho (`#064B20`) con texto en Blanco (`#FFFFFF`)[cite: 3].
* **Botones CTA Principales:** Fondo Amarillo Cachimba (`#FFD500`), texto Verde Rancho (`#064B20`), bordes redondeados y estado `:hover` en Amarillo Dorado (`#EFB900`)[cite: 3]. (Uso: *"Reservar"*, *"Conocer más"*, *"Comprar"*, *"Ver actividades"*)[cite: 3].
* **Tarjetas e Informativos:** Fondo Verde Muy Claro (`#EAF4EC`)[cite: 3].
* **Texto y Tipografía:** Títulos y párrafos en Carbón (`#172019`)[cite: 3].

---

## 3. Guía de Redes Sociales y Gráfica Digital

* **Distribución Recomendada:** 60% Verde/Blanco | 30% Verde Claro/Carbón | 10% Amarillo (Acentos y CTAs)[cite: 3].
* **Foco del Amarillo:** Utilizar exclusivamente para captar atención en títulos cortos, precios, botones, llamadas a la acción, íconos o marcos[cite: 3]. No saturar la composición con este color[cite: 3].
* **Consistencia:** El Verde Rancho (`#064B20`) debe sostener la identidad de la marca tanto en entornos digitales como físicos[cite: 3].

---

## 4. Configuración para Tailwind CSS (`tailwind.config.js`)

Para asegurar que los agentes e IA utilicen las clases correctas sin generar valores hexadecimales huérfanos, mapear los tokens en la configuración:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        cachimba: {
          'green-main': '#064B20',   // Verde Rancho
          'green-forest': '#0B642B', // Verde Bosque
          'green-light': '#EAF4EC',  // Verde Muy Claro
          'yellow-main': '#FFD500',  // Amarillo Cachimba
          'yellow-gold': '#EFB900',  // Amarillo Dorado
          'earth': '#6B4F32',        // Tierra
          'charcoal': '#172019',     // Carbón
        }
      }
    }
  }
}