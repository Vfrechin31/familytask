import { ref } from 'vue'
import apiFetch from './api.js'

// Membre actuellement connecté, partagé entre le garde de navigation (router/index.js)
// et App.vue pour éviter d'appeler /api/me deux fois au chargement d'une page
export const currentMember = ref(null)

// Vérifie que le token stocké dans localStorage correspond bien à un membre valide,
// en interrogeant /api/me. Met à jour currentMember et nettoie le token s'il est périmé.
export async function fetchCurrentMember() {
  const token = localStorage.getItem('token')
  if (!token) {
    currentMember.value = null
    return null
  }

  try {
    const response = await apiFetch('/me')
    if (!response.ok) throw new Error('Token invalide')

    currentMember.value = await response.json()
    return currentMember.value
  } catch (error) {
    // Token absent, périmé ou API injoignable : on nettoie la session locale
    localStorage.removeItem('token')
    currentMember.value = null
    return null
  }
}

// Nettoie l'état local du membre connecté (utilisé à la déconnexion)
export function clearCurrentMember() {
  localStorage.removeItem('token')
  currentMember.value = null
}
