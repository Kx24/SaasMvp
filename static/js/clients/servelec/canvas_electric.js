/**
 * canvas_electric.js — Red eléctrica animada
 * Cliente: Servelec Ingeniería
 *
 * Cargado únicamente en páginas que incluyen servelec/components/hero.html
 * No depende de librerías externas. Canvas API pura.
 */
(function () {
    'use strict';

    const canvas = document.getElementById('electricCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    const NODE_COUNT = 90;   // Más nodos
    const MAX_DIST   = 140;  // Menor distancia para más densidad

    let nodes  = [];
    let pulses = [];

    function randomBetween(a, b) {
        return a + Math.random() * (b - a);
    }

    function resize() {
        canvas.width  = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }

    function init() {
        nodes  = [];
        pulses = [];
        for (let i = 0; i < NODE_COUNT; i++) {
            nodes.push({
                x:       randomBetween(0, canvas.width),
                y:       randomBetween(0, canvas.height),
                vx:      randomBetween(-0.25, 0.25), // Más velocidad
                vy:      randomBetween(-0.18, 0.18),
                r:       randomBetween(1.5, 3.2),
                opacity: randomBetween(0.4, 1),
            });
        }
    }

    function spawnPulse() {
        const from       = Math.floor(Math.random() * nodes.length);
        const candidates = [];

        for (let j = 0; j < nodes.length; j++) {
            if (j === from) continue;
            const dx   = nodes[from].x - nodes[j].x;
            const dy   = nodes[from].y - nodes[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < MAX_DIST) candidates.push(j);
        }

        if (candidates.length === 0) return;

        const to = candidates[Math.floor(Math.random() * candidates.length)];
        pulses.push({ from, to, t: 0, speed: randomBetween(0.012, 0.028) });
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Mover nodos
        for (const n of nodes) {
            n.x += n.vx;
            n.y += n.vy;
            if (n.x < -20)               n.x = canvas.width  + 20;
            if (n.x > canvas.width  + 20) n.x = -20;
            if (n.y < -20)               n.y = canvas.height + 20;
            if (n.y > canvas.height + 20) n.y = -20;
        }

        // Dibujar cables
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dx   = nodes[i].x - nodes[j].x;
                const dy   = nodes[i].y - nodes[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MAX_DIST) {
                    const alpha = (1 - dist / MAX_DIST) * 0.35; // Más brillo
                    ctx.beginPath();
                    ctx.moveTo(nodes[i].x, nodes[i].y);
                    ctx.lineTo(nodes[j].x, nodes[j].y);
                    ctx.strokeStyle = `rgba(29, 185, 84, ${alpha})`;
                    ctx.lineWidth   = 1.2; // Más grosor
                    ctx.stroke();
                }
            }
        }

        // Dibujar pulsos
        pulses = pulses.filter(p => p.t <= 1);
        for (const p of pulses) {
            p.t += p.speed;
            const nx  = nodes[p.from].x + (nodes[p.to].x - nodes[p.from].x) * p.t;
            const ny  = nodes[p.from].y + (nodes[p.to].y - nodes[p.from].y) * p.t;
            const grd = ctx.createRadialGradient(nx, ny, 0, nx, ny, 12);
            grd.addColorStop(0, 'rgba(29, 185, 84, 0.75)');
            grd.addColorStop(1, 'rgba(29, 185, 84, 0)');

            ctx.beginPath();
            ctx.arc(nx, ny, 12, 0, Math.PI * 2);
            ctx.fillStyle = grd;
            ctx.fill();

            ctx.beginPath();
            ctx.arc(nx, ny, 2.8, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255, 255, 255, 0.95)'; // Más brillante
            ctx.fill();
        }

        // Dibujar nodos con resplandor
        for (const n of nodes) {
            const glow = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 4);
            glow.addColorStop(0, `rgba(29, 185, 84, ${n.opacity * 0.4})`);
            glow.addColorStop(1, 'rgba(29, 185, 84, 0)');
            ctx.fillStyle = glow;
            ctx.fillRect(n.x - n.r*4, n.y - n.r*4, n.r*8, n.r*8);

            ctx.beginPath();
            ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(29, 185, 84, ${n.opacity * 0.8})`;
            ctx.fill();
        }

        requestAnimationFrame(draw);
    }

    // Inicializar
    resize();
    init();
    draw();
    setInterval(spawnPulse, 1200); // Más frecuencia

    window.addEventListener('resize', () => {
        resize();
        init();
    });
})();