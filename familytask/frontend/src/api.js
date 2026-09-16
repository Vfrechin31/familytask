const BASE_URL = '/api'

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