<script setup lang="ts">
interface Branch {
  id: number
  name: string
  city: string
  address: string
  latitude: string
  longitude: string
  working_hours: string
}

const props = defineProps<{
  branches: Branch[]
  selectedBranchId: number | null
}>()

const emit = defineEmits<{
  (e: 'select', branch: Branch): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
let map: any = null
let markers: any[] = []

const ASTANA_CENTER: [number, number] = [51.1694, 71.4491]
const ASTANA_BOUNDS: [[number, number], [number, number]] = [
  [50.95, 71.15],
  [51.28, 71.65],
]

const initMap = async () => {
  if (!process.client || !mapContainer.value || !props.branches.length) return

  const L = (await import('leaflet')).default
  const bounds = L.latLngBounds(ASTANA_BOUNDS)

  map = L.map(mapContainer.value, {
    zoomControl: true,
    maxBounds: bounds,
    maxBoundsViscosity: 1,
    minZoom: 10,
  }).setView(ASTANA_CENTER, 11)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map)

  map.fitBounds(bounds, { padding: [16, 16] })

  renderMarkers(L)
}

const renderMarkers = (L: any) => {
  // Очищаем старые маркеры
  markers.forEach(m => m.remove())
  markers = []

  props.branches.forEach(branch => {
    const isSelected = branch.id === props.selectedBranchId
    const iconHtml = `
      <div style="
        width: ${isSelected ? 36 : 28}px;
        height: ${isSelected ? 36 : 28}px;
        background: ${isSelected ? '#e07b39' : '#1e293b'};
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: all 0.2s;
      "></div>
    `
    const icon = L.divIcon({
      html: iconHtml,
      className: '',
      iconSize: [isSelected ? 36 : 28, isSelected ? 36 : 28],
      iconAnchor: [isSelected ? 18 : 14, isSelected ? 36 : 28],
    })

    const marker = L.marker(
      [parseFloat(branch.latitude), parseFloat(branch.longitude)],
      { icon }
    )
      .addTo(map)
      .on('click', () => emit('select', branch))

    marker.bindPopup(`
      <div style="font-family: sans-serif; min-width: 180px;">
        <p style="font-weight: 700; margin: 0 0 4px;">${branch.name}</p>
        <p style="color: #64748b; font-size: 12px; margin: 0 0 2px;">📍 ${branch.address}</p>
        <p style="color: #64748b; font-size: 12px; margin: 0;">🕐 ${branch.working_hours}</p>
      </div>
    `)

    markers.push(marker)
  })
}

// Перерендер маркеров при смене выбранного филиала
watch(() => props.selectedBranchId, async () => {
  if (!map) return
  const L = (await import('leaflet')).default
  renderMarkers(L)
  // Центрируем карту на выбранном филиале
  const selected = props.branches.find(b => b.id === props.selectedBranchId)
  if (selected) {
    map.flyTo([parseFloat(selected.latitude), parseFloat(selected.longitude)], 13, { duration: 0.8 })
  }
})

onMounted(() => {
  nextTick(initMap)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div ref="mapContainer" class="branch-map" />
</template>

<style scoped>
.branch-map {
  width: 100%;
  height: 280px;
  border-radius: 16px;
  overflow: hidden;
  z-index: 0;
}

@media (min-width: 640px) {
  .branch-map {
    height: 360px;
  }
}
</style>
