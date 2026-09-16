import { ref } from 'vue'

// Thème actuel ('light' ou 'dark'), partagé dans toute l'app
const stored = localStorage.getItem('theme')
const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

export const isDark = ref(stored ? stored === 'dark' : systemPrefersDark)

// Applique la classe "dark" sur <html>, ce que style.css utilise pour ses variables de couleur
const applyTheme = () => {
  document.documentElement.classList.toggle('dark', isDark.value)
}

applyTheme()

// Bascule le thème et mémorise le choix explicite de l'utilisateur (prioritaire sur les réglages système)
export function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}
