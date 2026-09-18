// Adresse du back-end, injectée au build via VITE_API_URL. La propriété "host" de Render ne
// donne que le label court du service (ex. familytask-api-nzx3), sans schéma ni suffixe de domaine :
// on reconstitue nous-mêmes l'URL complète en https://<label>.onrender.com
// Chaîne vide par défaut : en local, le préfixe relatif /api suffit, le dev server Vite le proxy vers le conteneur backend
const apiHost = import.meta.env.VITE_API_URL
const BASE_URL = apiHost ? `https://${apiHost}.onrender.com/api` : '/api'

// Fonction centralisée pour tous les appels à l'API : ajoute automatiquement le token si présent
async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem('token')

  // On fusionne les en-têtes par défaut avec ceux éventuellement fournis par l'appelant
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  // On n'ajoute l'en-tête Authorization que si un token existe
  // (utile pour /signup et /login, qui n'ont pas encore de token)
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers
  })

  return response
}

export default apiFetch