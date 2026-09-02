# Propuestas de UI/UX: Soluciones para el Logo en el Navbar

**Proyecto:** Rancho Interactivo Cachimba  
**Documento de referencia:** `docs/design/propuestas_logo_navbar.md`  
**Problema:** El logo oficial de Rancho Cachimba posee un alto nivel de detalle ilustrativo y texto pequeño en curva. Al escalarlo dentro de un navbar estándar (40-60px), se vuelve difícil de leer. Incrementar el tamaño vertical de todo el navbar rompe la proporción de la pantalla y reduce el área útil del contenido (viewport).

---

## Estrategia General de Solución

1. **Eliminar redundancia de texto:** En el HTML original figuraba el imagotipo e inmediatamente al lado la etiqueta `RanchoCachimba` en texto plano. La ilustración ya contiene el nombre de la marca; la duplicación ocupa espacio horizontal innecesario.
2. **Desacoplar la altura del logo de la altura de la barra:** Aplicar técnicas de desbordamiento controlado (overflow/floating) o arquitectura a dos niveles para dar respiro al imagotipo.

---

## Alternativa 1: Logo "Floating Badge" (Sobresaliente) — *Recomendada*

### Concepto
El navbar mantiene un alto compacto (`h-16`), pero el contenedor del logo rompe el margen inferior sobresaliendo ligeramente hacia la sección del Hero (`-mb-6` o `-mb-8`).

### Ventajas
- Mantiene la barra de navegación delgada y limpia.
- Permite agrandar la imagen hasta más del doble de su tamaño sin afectar a los links de navegación ni a los botones.
- Otorga un carácter orgánico y distintivo muy utilizado en marcas de turismo, gastronomía y áreas rurales.

### Código de Implementación (Tailwind CSS)

```html
<header class="sticky top-0 z-50 bg-white border-b border-slate-100 shadow-sm">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      
      <!-- Contenedor con margen negativo para permitir el desborde -->
      <div class="flex-shrink-0 relative z-10 flex items-center">
        <a href="/" class="block -mb-6 transition-transform hover:scale-105">
          <img 
            src="{% static 'images/logo-cachimba.png' %}" 
            alt="Rancho Cachimba" 
            class="h-24 w-auto bg-white p-1 rounded-b-xl drop-shadow-md"
          >
        </a>
      </div>

      <!-- Menú de navegación -->
      <nav class="hidden md:flex items-center space-x-8">
        <a href="#" class="text-[#172019] hover:text-[#064B20] text-sm font-medium">Inicio</a>
        <a href="#" class="text-[#172019] hover:text-[#064B20] text-sm font-medium">Nosotros</a>
        <a href="#" class="text-[#172019] hover:text-[#064B20] text-sm font-medium">Servicios</a>
        <a href="#" class="text-[#172019] hover:text-[#064B20] text-sm font-medium">Contacto</a>
      </nav>

      <!-- CTA Principal -->
      <div class="hidden md:flex items-center space-x-4">
        <a href="#" class="bg-[#FFD500] hover:bg-[#EFB900] text-[#064B20] font-bold px-5 py-2.5 rounded-lg text-sm transition-colors shadow-sm">
          Reservar Visita
        </a>
      </div>

    </div>
  </div>
</header>