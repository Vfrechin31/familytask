<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import apiFetch from './api.js'
import { currentMember, clearCurrentMember } from './auth.js'
import { isDark, toggleTheme } from './theme.js'
import Avatar from './components/Avatar.vue'

const router = useRouter()

// Prénom du membre connecté, dérivé de l'état partagé (currentMember) déjà rempli
// par le garde de navigation via /api/me — pas besoin de refaire l'appel ici
const memberName = computed(() => currentMember.value?.name || '')

// Le membre connecté est-il administrateur ? Utilisé pour afficher ou non l'onglet "Famille"
const isAdmin = computed(() => currentMember.value?.is_admin || false)

// Déconnexion : on tente de prévenir le serveur, mais on déconnecte localement dans tous les cas
const handleLogout = async () => {
  try {
    // On informe le serveur pour qu'il invalide le token côté base de données
    await apiFetch('/logout', { method: 'POST' })
  } catch (error) {
    // Si le serveur est injoignable (panne réseau, backend éteint...), on ne bloque pas l'utilisateur :
    // mieux vaut le déconnecter localement que le laisser coincé sur l'app
    console.error('Impossible de joindre le serveur pour la déconnexion', error)
  }

  // Dans tous les cas (succès ou échec de l'appel réseau), on nettoie la session locale
  clearCurrentMember()
  router.push('/login')
}
</script>

<template>
  <div class="app-frame">
    <div class="app-screen">
      <!-- La barre du haut ne s'affiche que si un membre est connecté -->
      <header v-if="memberName" class="top-bar">
        <span class="top-bar-user">
          <Avatar :name="memberName" :size="32" />
          {{ memberName }}
        </span>
        <span class="top-bar-actions">
          <button
            @click="toggleTheme"
            class="theme-toggle-btn"
            :title="isDark ? 'Passer en mode clair' : 'Passer en mode sombre'"
          >{{ isDark ? '☀️' : '🌙' }}</button>
          <button @click="handleLogout" class="logout-btn">Se déconnecter</button>
        </span>
      </header>

      <router-view />

      <!-- Barre d'onglets en bas, toujours visible (sticky) tant qu'un membre est connecté -->
      <nav v-if="memberName" class="tab-bar">
        <router-link to="/tasks" class="tab-link">📋 Tâches</router-link>
        <!-- L'onglet Famille n'apparaît que pour les administrateurs -->
        <router-link v-if="isAdmin" to="/famille" class="tab-link">👪 Famille</router-link>
      </nav>
    </div>
  </div>
</template>

<style scoped>
/* Fond "hors écran" derrière le cadre téléphone, visible uniquement sur grand écran */
.app-frame {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-screen {
  position: relative;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--bg-page);
  -webkit-overflow-scrolling: touch;
}

/* Sur grand écran, on simule un vrai téléphone : cadre fixe, coins arrondis, ombre marquée */
@media (min-width: 700px) and (min-height: 700px) {
  .app-screen {
    width: 430px;
    height: 900px;
    max-height: 92vh;
    border-radius: 44px;
    border: 10px solid #1c1c1f;
    box-shadow: 0 40px 80px rgba(0, 0, 0, 0.5), 0 10px 24px rgba(0, 0, 0, 0.3);
  }
}

.top-bar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: rgba(122, 168, 109, 0.1);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(31, 41, 55, 0.08);
}

.top-bar-user {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-dark, #1f2937);
}

.top-bar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.theme-toggle-btn {
  padding: 6px 10px;
  background: var(--bg-white, #ffffff);
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--btn-shadow);
}

.theme-toggle-btn:hover {
  transform: translateY(-3px);
  box-shadow: var(--btn-shadow-hover);
}

.theme-toggle-btn:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

.logout-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #7aa86d 0%, #6b8e71 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--btn-shadow);
}

.logout-btn:hover {
  transform: translateY(-3px);
  box-shadow: var(--btn-shadow-hover);
}

.logout-btn:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

.tab-bar {
  position: sticky;
  bottom: 0;
  z-index: 5;
  display: flex;
  background: var(--bg-white, #ffffff);
  box-shadow: 0 -10px 26px rgba(31, 41, 55, 0.16), 0 -2px 6px rgba(122, 168, 109, 0.15);
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.tab-link {
  flex: 1;
  text-align: center;
  padding: 14px 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted, #6b7280);
  text-decoration: none;
  transition: color 0.2s ease;
}

.tab-link:hover {
  color: #6b8e71;
}

/* vue-router ajoute automatiquement cette classe au lien actif */
.tab-link.router-link-active {
  color: #7aa86d;
}
</style>