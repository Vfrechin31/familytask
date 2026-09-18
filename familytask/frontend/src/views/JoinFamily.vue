<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiFetch from '../api.js'

const router = useRouter()
const route = useRoute()

// Champs du formulaire pour rejoindre une famille existante
const familyCode = ref('')
const name = ref('')
const lien = ref('')
const email = ref('')
const password = ref('')

// Message d'erreur affiché si la tentative échoue
const errorMessage = ref('')

// Pré-remplit le code famille si présent dans le lien partagé (ex. /join?code=3F9A2C)
onMounted(() => {
  if (route.query.code) {
    familyCode.value = String(route.query.code).toUpperCase()
  }
})

// Fonction appelée à la soumission du formulaire
const handleJoin = async () => {
  errorMessage.value = ''

  try {
    const response = await apiFetch('/join', {
      method: 'POST',
      body: JSON.stringify({
        family_code: familyCode.value,
        name: name.value,
        lien: lien.value,
        email: email.value,
        password: password.value
      })
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || "Erreur lors de l'inscription")
    }

    // Même principe que Signup.vue : /api/join ne renvoie pas de token directement,
    // on enchaîne donc avec un login pour en récupérer un
    const loginResponse = await apiFetch('/login', {
      method: 'POST',
      body: JSON.stringify({ email: email.value, password: password.value })
    })

    const loginData = await loginResponse.json()
    localStorage.setItem('token', loginData.token)

    router.push('/tasks')
  } catch (error) {
    errorMessage.value = error.message
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-logo">🔗</div>
      <h1>Rejoindre une famille</h1>
      <p class="auth-subtitle">Entre le code transmis par un membre de ta famille</p>

      <form @submit.prevent="handleJoin" class="auth-form">
        <input v-model="familyCode" type="text" placeholder="Code famille (ex. 3F9A2C)" required />
        <input v-model="name" type="text" placeholder="Prénom" required />
        <input v-model="lien" type="text" placeholder="Lien de parenté (ex. Fille, Fils)" required />
        <input v-model="email" type="email" placeholder="Email" required />
        <input v-model="password" type="password" placeholder="Mot de passe" required />

        <div v-if="errorMessage" class="error-message">⚠️ {{ errorMessage }}</div>

        <button type="submit">Rejoindre la famille</button>
      </form>

      <router-link to="/signup" class="auth-link">Créer une nouvelle famille à la place</router-link>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background: linear-gradient(160deg, #7aa86d 0%, var(--bg-page) 45%);
}

.auth-container {
  width: 100%;
  max-width: 360px;
  padding: 36px 28px;
  text-align: center;
  background: var(--bg-white, #ffffff);
  border-radius: 24px;
  box-shadow: var(--card-shadow-hover);
}

.auth-logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  border-radius: 20px;
  background: linear-gradient(135deg, #7aa86d 0%, #f5d5b8 100%);
  box-shadow: 0 8px 18px rgba(122, 168, 109, 0.35);
}

.auth-container h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text-dark, #1f2937);
}

.auth-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-muted, #6b7280);
}

.auth-link {
  display: inline-block;
  margin-top: 20px;
  font-size: 13px;
  font-weight: 600;
  color: var(--primary, #7aa86d);
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 24px 0;
}

.auth-form input {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  box-shadow: inset 0 2px 5px rgba(31, 41, 55, 0.08);
}

.auth-form button {
  padding: 12px 20px;
  background: linear-gradient(135deg, #7aa86d 0%, #6b8e71 100%);
  color: white;
  border: none;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--btn-shadow);
}

.auth-form button:hover {
  transform: translateY(-3px);
  box-shadow: var(--btn-shadow-hover);
}

.auth-form button:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

.error-message {
  padding: 12px 16px;
  background: #fee2e2;
  border-left: 4px solid #dc2626;
  border-radius: 8px;
  color: #7f1d1d;
  font-weight: 600;
  font-size: 14px;
}
</style>
