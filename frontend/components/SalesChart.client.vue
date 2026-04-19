<script setup lang="ts">
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from "chart.js";
import { Line } from "vue-chartjs";
import { computed } from "vue";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const props = defineProps<{
  labels: string[];
  data: number[];
  labelName?: string;
  colorHex?: string;
}>();

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: "index" as const,
    intersect: false,
  },
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: "#1e293b",
      padding: 12,
      titleFont: { size: 14, family: "'Inter', sans-serif" },
      bodyFont: { size: 14, family: "'Inter', sans-serif" },
      displayColors: false,
      cornerRadius: 8,
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: "#f1f5f9",
        drawBorder: false,
      },
      ticks: {
        font: { family: "'Inter', sans-serif", size: 12 },
        color: "#64748b"
      }
    },
    x: {
      grid: {
        display: false,
        drawBorder: false,
      },
      ticks: {
        font: { family: "'Inter', sans-serif", size: 12 },
        color: "#64748b",
        maxRotation: 45,
        minRotation: 45
      }
    }
  }
};

const chartData = computed(() => {
  const color = props.colorHex || "#0ea5e9";
  return {
    labels: props.labels,
    datasets: [
      {
        label: props.labelName || "Значение",
        data: props.data,
        borderColor: color,
        backgroundColor: `${color}15`, // добавим прозрачность для заливки (hex)
        borderWidth: 2,
        pointBackgroundColor: "#ffffff",
        pointBorderColor: color,
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.4 // гладкие кривые
      }
    ]
  };
});
</script>

<template>
  <div class="h-80 w-full relative">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
