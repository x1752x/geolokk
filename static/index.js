const MAX_POINTS = 4000;
const WINDOW_SIZE = 25;
let counter = 0;

const sensorPlots = {};
const sensorAnnotations = {};

function initSensorPlot(sensorId, container) {
    const data = [[], []]; // [x[], y[]]
    
    const opts = {
        width: 800,
        height: 150,
        pxAlign: false,
        scales: {
            x: { time: false },
            y: { range: [-800, 800] }
        },
        series: [
            {},
            {
                stroke: '#0D6EFD',
                width: 1,
                fill: null,
                points: { show: false }
            }
        ],
        axes: [
            {
                values: (u, vals) => vals.map(v => parseFloat(v).toFixed(1)),
                grid: { stroke: 'rgba(0,0,0,0.1)' },
                ticks: { stroke: 'rgba(0,0,0,0.1)' },
                font: '12px sans-serif',
                stroke: 'black'
            },
            {
                grid: { stroke: 'rgba(0,0,0,0.1)' },
                ticks: { stroke: 'rgba(0,0,0,0.1)' },
                font: '12px sans-serif',
                stroke: 'black'
            }
        ],
        cursor: { show: false },
        legend: { show: false },
        hooks: {
            draw: [
                u => {
                    const annotations = sensorAnnotations[sensorId] || [];
                    if (!annotations.length) return;
                    
                    const ctx = u.ctx;
                    ctx.save();
                    ctx.strokeStyle = 'red';
                    ctx.lineWidth = 2;
                    ctx.setLineDash([6, 6]);
                    
                    annotations.forEach(xVal => {
                        const px = u.valToPos(xVal, 'x', true);
                        if (px === null) return;
                        
                        // Вертикальная линия
                        ctx.beginPath();
                        ctx.moveTo(px, u.bbox.top);
                        ctx.lineTo(px, u.bbox.top + u.bbox.height);
                        ctx.stroke();
                        
                        // Подпись (опционально)
                        ctx.fillStyle = 'red';
                        ctx.fillRect(px - 20, u.bbox.top, 40, 14);
                        ctx.fillStyle = 'white';
                        ctx.font = '8px sans-serif';
                        ctx.textAlign = 'center';
                        ctx.fillText(xVal.toFixed(2), px, u.bbox.top + 10);
                    });
                    
                    ctx.restore();
                }
            ]
        }
    };
    
    return new uPlot(opts, data, container);
}

function initAllSensors() {
    if (!window.SENSOR_IDS || !Array.isArray(window.SENSOR_IDS)) {
        console.warn('SENSOR_IDS не определён');
        return;
    }
    
    window.SENSOR_IDS.forEach(sensorId => {
        const container = document.getElementById(`sensor_${sensorId}`);
        if (!container) return;
        
        sensorPlots[sensorId] = initSensorPlot(sensorId, container);
        sensorAnnotations[sensorId] = [];
    });
}


function handleWebSocketMessage(data) {
    // 1. Приём и накопление данных
    Object.keys(data.sensor_responses).forEach(sensorId => {
        const plot = sensorPlots[sensorId];
        if (!plot) return;

        const [xData, yData] = plot.data;
        xData.push(counter);
        yData.push(data.sensor_responses[sensorId]);

        // Скользящее окно
        if (xData.length > MAX_POINTS) {
            xData.shift();
            yData.shift();
        }

        // Аннотации
        if (data.event_marks.includes(Number(sensorId))) {
            sensorAnnotations[sensorId].push(counter);
            if (sensorAnnotations[sensorId].length > 100) {
                sensorAnnotations[sensorId].shift();
            }
        }
    });

    if (data.location.length != 0) {
        if (window.clusterChart.data.datasets[1].length < 1) {
            window.clusterChart.data.datasets[1].data.push({x: data.location[0], y: data.location[1]})
        } else {
            window.clusterChart.data.datasets[1].data[0] = {x: data.location[0], y: data.location[1]};
        }
        window.clusterChart.update();
    }

    // 2. Отрисовка только в активной вкладке (экономит ресурсы)
    if (!document.hidden) {
        Object.keys(data.sensor_responses).forEach(sensorId => {
            const plot = sensorPlots[sensorId];
            if (!plot) return;
            
            plot.setData(plot.data, false); // используем существующие ссылки
            plot.setScale('x', { min: counter - WINDOW_SIZE, max: counter });
        });
    }

    counter += 0.01;
}

// === Обработчик переключения вкладок ===
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Вкладка стала активной: принудительно перерисовываем все графики
        Object.values(sensorPlots).forEach(plot => {
            plot.setData(plot.data, false);
            plot.setScale('x', { min: counter - WINDOW_SIZE, max: counter });
        });
    }
});

// === Точка входа ===
document.addEventListener('DOMContentLoaded', () => {
    initAllSensors();
    
    const ws = new WebSocket("ws://localhost:8000/impulse");
    
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error('Ошибка парсинга WebSocket:', e);
        }
    };
    
    ws.onerror = function(err) {
        console.error('WebSocket error:', err);
    };
});