vue
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import apiFetch from '../api.js'

const router = useRouter()

const email = ref('')
const password = ref('')
const errorMessage = ref('')

const handleLogin = async () => {
  errorMessage.value = ''

  try {
    const response = await apiFetch('/login', {
      method: 'POST',
      body: JSON.stringify({ email: email.value, password: password.value })
    })

    if (!response.ok) {
      // Ta route /api/login renvoie 401 avec un message neutre en cas d'échec
      throw new Error('Email ou mot de passe incorrect')
    }

    const data = await response.json()
    localStorage.setItem('token', data.token)

    router.push('/tasks')
  } catch (error) {
    errorMessage.value = error.message
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-logo">👨‍👩‍👧‍👦</div>
      <h1>Connexion</h1>
      <p class="auth-subtitle">Contente de te revoir !</p>

      <form @submit.prevent="handleLogin" class="auth-form">
        <input v-model="email" type="email" placeholder="Email" required />
        <input v-model="password" type="password" placeholder="Mot de passe" required />

        <div v-if="errorMessage" class="error-message">⚠️ {{ errorMessage }}</div>

        <button type="submit">Se connecter</button>
      </form>

      <router-link to="/signup" class="auth-link">Pas encore de compte ? Créer ma famille</router-link>
      <router-link to="/join" class="auth-link">On t'a transmis un code ? Rejoindre une famille</router-link>
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