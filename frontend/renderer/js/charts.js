/* ══════════════════════════════════════════════════════
   CHARTS.JS — Chart.js Wrapper with Dark Theme
   ══════════════════════════════════════════════════════ */

const Charts = (() => {
  const instances = {};

  /* ─── Dark Theme Defaults ─── */
  const DARK_THEME = {
    color: '#94a3b8',
    borderColor: 'rgba(148, 163, 184, 0.1)',
    backgroundColor: 'transparent',
  };

  const COLORS = {
    primary:  { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6' },
    success:  { bg: 'rgba(34, 197, 94, 0.15)',  border: '#22c55e' },
    danger:   { bg: 'rgba(239, 68, 68, 0.15)',  border: '#ef4444' },
    warning:  { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b' },
    purple:   { bg: 'rgba(139, 92, 246, 0.15)', border: '#8b5cf6' },
    cyan:     { bg: 'rgba(6, 182, 212, 0.15)',   border: '#06b6d4' },
  };

  const PALETTE = [
    COLORS.primary.border,
    COLORS.success.border,
    COLORS.danger.border,
    COLORS.warning.border,
    COLORS.purple.border,
    COLORS.cyan.border,
  ];

  const PALETTE_BG = [
    COLORS.primary.bg,
    COLORS.success.bg,
    COLORS.danger.bg,
    COLORS.warning.bg,
    COLORS.purple.bg,
    COLORS.cyan.bg,
  ];

  /* ─── Configure Chart.js Defaults ─── */
  function configureDefaults() {
    if (!window.Chart) return;

    Chart.defaults.color = DARK_THEME.color;
    Chart.defaults.borderColor = DARK_THEME.borderColor;
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
    Chart.defaults.plugins.legend.labels.padding = 16;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.95)';
    Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 13 };
    Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(148, 163, 184, 0.15)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.displayColors = true;
    Chart.defaults.plugins.tooltip.boxPadding = 4;
    Chart.defaults.animation = {
      duration: 800,
      easing: 'easeOutQuart',
    };
  }

  /* ─── Destroy existing chart ─── */
  function destroy(chartId) {
    if (instances[chartId]) {
      instances[chartId].destroy();
      delete instances[chartId];
    }
  }

  /* ─── Line Chart ─── */
  function createLineChart(canvasId, data = {}, options = {}) {
    destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.labels || [],
        datasets: (data.datasets || [{ data: data.values || [] }]).map((ds, i) => ({
          label: ds.label || 'Value',
          data: ds.data || [],
          borderColor: ds.borderColor || PALETTE[i % PALETTE.length],
          backgroundColor: ds.backgroundColor || PALETTE_BG[i % PALETTE_BG.length],
          borderWidth: 2,
          fill: ds.fill !== undefined ? ds.fill : true,
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: ds.borderColor || PALETTE[i % PALETTE.length],
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          ...ds,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: data.datasets && data.datasets.length > 1,
            position: 'top',
            align: 'end',
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              maxRotation: 0,
              maxTicksLimit: 8,
            },
          },
          y: {
            grid: {
              color: 'rgba(148, 163, 184, 0.07)',
            },
            ticks: {
              padding: 8,
            },
            beginAtZero: true,
          },
        },
        ...options,
      },
    });

    instances[canvasId] = chart;
    return chart;
  }

  /* ─── Pie Chart ─── */
  function createPieChart(canvasId, data = {}, options = {}) {
    destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const chart = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: data.labels || [],
        datasets: [{
          data: data.values || [],
          backgroundColor: data.colors || PALETTE,
          borderColor: 'rgba(15, 23, 42, 0.8)',
          borderWidth: 2,
          hoverBorderColor: '#fff',
          hoverBorderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 16,
            },
          },
        },
        ...options,
      },
    });

    instances[canvasId] = chart;
    return chart;
  }

  /* ─── Bar Chart ─── */
  function createBarChart(canvasId, data = {}, options = {}) {
    destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.labels || [],
        datasets: (data.datasets || [{ data: data.values || [] }]).map((ds, i) => ({
          label: ds.label || 'Value',
          data: ds.data || [],
          backgroundColor: ds.backgroundColor || PALETTE_BG[i % PALETTE_BG.length],
          borderColor: ds.borderColor || PALETTE[i % PALETTE.length],
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 40,
          ...ds,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: data.datasets && data.datasets.length > 1,
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
          },
          y: {
            grid: {
              color: 'rgba(148, 163, 184, 0.07)',
            },
            beginAtZero: true,
          },
        },
        ...options,
      },
    });

    instances[canvasId] = chart;
    return chart;
  }

  /* ─── Doughnut Chart ─── */
  function createDoughnutChart(canvasId, data = {}, options = {}) {
    destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: data.labels || [],
        datasets: [{
          data: data.values || [],
          backgroundColor: data.colors || PALETTE,
          borderColor: 'rgba(15, 23, 42, 0.8)',
          borderWidth: 3,
          hoverBorderColor: '#fff',
          hoverBorderWidth: 2,
          spacing: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 16,
            },
          },
        },
        ...options,
      },
    });

    instances[canvasId] = chart;
    return chart;
  }

  /* ─── Update Chart Data ─── */
  function updateChart(chartId, newData) {
    const chart = instances[chartId];
    if (!chart) return;

    if (newData.labels) {
      chart.data.labels = newData.labels;
    }

    if (newData.datasets) {
      newData.datasets.forEach((ds, i) => {
        if (chart.data.datasets[i]) {
          Object.assign(chart.data.datasets[i], ds);
        }
      });
    }

    if (newData.values && chart.data.datasets[0]) {
      chart.data.datasets[0].data = newData.values;
    }

    chart.update('active');
  }

  /* ─── Get instance ─── */
  function get(chartId) {
    return instances[chartId] || null;
  }

  /* ─── Destroy all ─── */
  function destroyAll() {
    Object.keys(instances).forEach(destroy);
  }

  // Configure defaults on load
  configureDefaults();

  return {
    createLineChart,
    createPieChart,
    createBarChart,
    createDoughnutChart,
    updateChart,
    destroy,
    destroyAll,
    get,
    COLORS,
    PALETTE,
    PALETTE_BG,
    configureDefaults,
  };
})();
