<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    default: ''
  },
  size: {
    type: Number,
    default: 36
  }
})

// Couleur stable dérivée du prénom (même personne = toujours la même couleur d'avatar)
const hue = computed(() => {
  let hash = 0
  for (const char of props.name) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360
  }
  return hash
})

const initial = computed(() => props.name.trim().charAt(0).toUpperCase() || '?')
</script>

<template>
  <span
    class="avatar"
    :style="{
      width: size + 'px',
      height: size + 'px',
      fontSize: Math.round(size * 0.42) + 'px',
      background: `hsl(${hue}, 60%, 55%)`
    }"
  >{{ initial }}</span>
</template>

<style scoped>
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 50%;
  color: white;
  font-weight: 700;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
</style>
