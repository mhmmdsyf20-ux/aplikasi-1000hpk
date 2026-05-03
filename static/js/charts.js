/**
 * charts.js — Visualisasi data imunisasi menggunakan Chart.js 4.x
 * Memuat data dari endpoint JSON /api/chart/*
 */

// Warna konsisten sesuai design spec
const COLORS = {
    selesai:   '#28a745',
    mendatang: '#ffc107',
    terlewat:  '#dc3545',
    info:      '#007bff',
    terjadwal: '#0d6efd',
};

/**
 * Inisialisasi donut chart status imunisasi di dashboard.
 * Data diambil dari endpoint GET /api/chart/status
 */
async function initChartStatus() {
    const canvas = document.getElementById('chartStatus');
    if (!canvas) return;

    try {
        const resp = await fetch('/anak/api/chart/status');
        if (!resp.ok) return;
        const data = await resp.json();

        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Selesai', 'Terjadwal', 'Terlewat'],
                datasets: [{
                    data: [data.selesai, data.terjadwal, data.terlewat],
                    backgroundColor: [COLORS.selesai, COLORS.terjadwal, COLORS.terlewat],
                    borderWidth: 2,
                    borderColor: '#fff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.label}: ${ctx.raw} imunisasi`
                        }
                    }
                }
            }
        });
    } catch (e) {
        console.warn('Chart status gagal dimuat:', e);
    }
}

/**
 * Inisialisasi bar chart imunisasi per bulan (6 bulan terakhir).
 * Data diambil dari endpoint GET /api/chart/bulanan
 */
async function initChartBulanan() {
    const canvas = document.getElementById('chartBulanan');
    if (!canvas) return;

    try {
        const resp = await fetch('/anak/api/chart/bulanan');
        if (!resp.ok) return;
        const data = await resp.json();

        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Imunisasi Selesai',
                    data: data.values,
                    backgroundColor: COLORS.selesai + 'CC',
                    borderColor: COLORS.selesai,
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.raw} imunisasi selesai`
                        }
                    }
                }
            }
        });
    } catch (e) {
        console.warn('Chart bulanan gagal dimuat:', e);
    }
}

// Jalankan saat DOM siap
document.addEventListener('DOMContentLoaded', () => {
    initChartStatus();
    initChartBulanan();
});
