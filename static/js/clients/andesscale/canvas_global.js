/**
 * AndesScale — canvas_global.js
 * Malla de nodos reactiva al pulso. Fijada en toda la página (position: fixed).
 * Pulsos emitidos desde el logo principal (#logo-principal).
 */
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const canvas = document.getElementById('globalCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        function resize() {
            canvas.width  = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resize();
        window.addEventListener('resize', () => { resize(); initGrid(); });

        /* ── Configuración ── */
        const SPACING            = 70;
        const MAX_CONNECTION_DIST = 110;
        const PULSE_INTERVAL     = 2200;

        let nodes  = [];
        let pulses = [];

        function getEmitter() {
            const el = document.getElementById('logo-principal');
            if (el) {
                const rect = el.getBoundingClientRect();
                return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
            }
            return { x: canvas.width * 0.5, y: canvas.height * 0.5 };
        }

        function initGrid() {
            nodes = [];
            const cols = Math.ceil(canvas.width  / SPACING);
            const rows = Math.ceil(canvas.height / SPACING);
            for (let x = 0; x <= cols; x++) {
                for (let y = 0; y <= rows; y++) {
                    nodes.push({ baseX: x * SPACING, baseY: y * SPACING, x: x * SPACING, y: y * SPACING, active: 0 });
                }
            }
        }
        initGrid();

        function spawnPulse() {
            const e = getEmitter();
            pulses.push({ x: e.x, y: e.y, radius: 0, speed: 1.5, maxRadius: Math.max(canvas.width, canvas.height) });
        }
        setInterval(spawnPulse, PULSE_INTERVAL);

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            pulses = pulses.filter(p => p.radius < p.maxRadius);
            for (const p of pulses) p.radius += p.speed;

            for (const node of nodes) {
                node.x = node.baseX;
                node.y = node.baseY;
                node.active *= 0.92;
                for (const p of pulses) {
                    const dx   = node.baseX - p.x;
                    const dy   = node.baseY - p.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    const diff = Math.abs(dist - p.radius);
                    if (diff < 40) {
                        const force = 1 - diff / 40;
                        if (dist !== 0) { node.x += (dx / dist) * force * 8; node.y += (dy / dist) * force * 8; }
                        node.active = Math.max(node.active, force);
                    }
                }
            }

            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx   = nodes[i].x - nodes[j].x;
                    const dy   = nodes[i].y - nodes[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < MAX_CONNECTION_DIST) {
                        const alpha = 0.08 + (nodes[i].active + nodes[j].active) * 0.35;
                        ctx.beginPath();
                        ctx.moveTo(nodes[i].x, nodes[i].y);
                        ctx.lineTo(nodes[j].x, nodes[j].y);
                        ctx.strokeStyle = `rgba(29, 78, 216, ${alpha})`;
                        ctx.lineWidth   = 1;
                        ctx.stroke();
                    }
                }
            }
            requestAnimationFrame(draw);
        }
        draw();
    });
})();
