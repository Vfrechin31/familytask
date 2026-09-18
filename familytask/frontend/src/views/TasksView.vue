<script setup>
import { ref, computed, onMounted } from 'vue'
import TaskList from '../components/TaskList.vue'
import ChatAssistant from '../components/ChatAssistant.vue'
import apiFetch from '../api.js'
import Avatar from '../components/Avatar.vue'

// Membre actuellement connecté, récupéré via /api/me (vrai système d'authentification)
const currentMember = ref(null)

// Adresse de base de l'API backend pour les tâches
const API_URL = '/tasks'

// Données réactives pour les tâches : vide au départ, remplie via l'API au montage
const tasks = ref([])

// Variable pour le nouveau titre de tâche
const newTask = ref('')

// État du dropdown de suggestions
const showSuggestions = ref(false)

// Message d'erreur affiché en cas de problème réseau/API
const errorMessage = ref('')

// Liste des membres de la famille, utilisée pour le menu "Pour qui ?" et les statistiques
const familyMembers = ref([])

// Id du membre sélectionné dans le menu déroulant ("" = "Pour moi")
const selectedMemberId = ref('')

// Statistiques de tâches effectuées par membre (calculées côté client, le backend ne stocke pas "completedBy")
const stats = ref({})

// Liste des tâches communes (suggestions)
const commonTasks = [
  'Faire les courses',
  'Faire la vaisselle',
  'Faire le ménage',
  'Faire le linge',
  'Faire les devoirs',
  'Faire du sport',
  'Faire un gâteau',
  'Faire le jardin',
  'Faire les lits',
  'Faire la poussière',
  'Faire les courses pour le déjeuner',
  'Faire une promenade',
  'Ranger la chambre de Cloé',
  "Ranger la chambre d'Olivia",
  'Faire les vitres',
  'Faire le tri dans les vêtements',
  'Faire le tri dans les jouets',
  'Faire le tri dans les livres',
]

// Récupère les infos du membre connecté via /api/me (vrai système d'authentification)
const fetchCurrentMember = async () => {
  try {
    const response = await apiFetch('/me')
    if (!response.ok) throw new Error('Token invalide')
    currentMember.value = await response.json()
  } catch (error) {
    console.error(error)
    currentMember.value = null
  }
}

// Calculer les permissions du membre connecté, basées sur le champ is_admin renvoyé par /api/me
const currentUserPermissions = computed(() => {
  if (!currentMember.value) {
    return {
      canCreateTasks: false,
      canDeleteTasks: false,
      canManageMembers: false,
      canValidateTasks: false
    }
  }

  const isAdmin = currentMember.value.is_admin
  return {
    canCreateTasks: true,
    canDeleteTasks: isAdmin,
    canManageMembers: isAdmin,
    canValidateTasks: true
  }
})

// Calculer les suggestions filtrées en fonction de ce qui est écrit
const suggestions = computed(() => {
  const existingTitles = tasks.value.map(t => t.title.toLowerCase())
  let filtered = commonTasks.filter(task => !existingTitles.includes(task.toLowerCase()))

  if (newTask.value.trim() === '') {
    return filtered.slice(0, 8)
  }

  const searchTerm = newTask.value.toLowerCase()
  return filtered
    .filter(task => task.toLowerCase().startsWith(searchTerm))
    .slice(0, 8)
})

// Récupère la liste complète des tâches depuis l'API et remplace l'état local
const fetchTasks = async () => {
  try {
    const response = await apiFetch(API_URL)
    if (!response.ok) throw new Error('Erreur lors du chargement des tâches')
    const data = await response.json()
    tasks.value = data
    errorMessage.value = ''
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de charger les tâches.'
  }
}

// Récupère la liste des membres de la famille (pour le menu "Pour qui ?" et les statistiques)
const fetchFamilyMembers = async () => {
  try {
    const response = await apiFetch('/members')
    if (!response.ok) throw new Error('Erreur lors du chargement des membres')
    const data = await response.json()
    familyMembers.value = data
  } catch (error) {
    console.error(error)
  }
}

// On récupère le membre connecté, puis les tâches et les membres de la famille au montage du composant
onMounted(async () => {
  await fetchCurrentMember()
  fetchTasks()
  fetchFamilyMembers()
})

// Ajoute une nouvelle tâche via l'API, puis recharge la liste à jour
const addTask = async () => {
  if (!currentUserPermissions.value.canCreateTasks) return
  if (newTask.value.trim() === '') return

  try {
    // On ne construit le champ member_id que si un membre autre que soi-même est sélectionné
    const body = { title: newTask.value }
    if (selectedMemberId.value !== '') {
      body.member_id = Number(selectedMemberId.value)
    }

    const response = await apiFetch(API_URL, {
      method: 'POST',
      body: JSON.stringify(body)
    })
    if (!response.ok) throw new Error("Erreur lors de l'ajout de la tâche")

    newTask.value = ''
    selectedMemberId.value = '' // On réinitialise le menu sur "Pour moi" après ajout
    showSuggestions.value = false
    await fetchTasks()
  } catch (error) {
    console.error(error)
    errorMessage.value = "Impossible d'ajouter la tâche."
  }
}

// Sélectionne une suggestion et l'ajoute automatiquement
const selectSuggestion = (task) => {
  if (!currentUserPermissions.value.canCreateTasks) return
  newTask.value = task
  showSuggestions.value = false
  addTask()
}

// Bascule l'état "done" d'une tâche via l'API (le serveur inverse la valeur), puis recharge la liste
const toggleTask = async (id) => {
  if (!currentUserPermissions.value.canValidateTasks) return

  try {
    const response = await apiFetch(`${API_URL}/${id}`, { method: 'PATCH' })
    if (!response.ok) throw new Error('Erreur lors de la mise à jour de la tâche')

    const updatedTask = await response.json()
    const memberName = currentMember.value.name
    if (updatedTask.done) {
      stats.value[memberName] = (stats.value[memberName] || 0) + 1
    } else {
      stats.value[memberName] = (stats.value[memberName] || 0) - 1
    }

    await fetchTasks()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de mettre à jour la tâche.'
  }
}

// Calculer les statistiques de tâches effectuées par personne
const taskStats = computed(() => {
  return stats.value
})

// Supprime une tâche via l'API, puis recharge la liste
const deleteTask = async (id) => {
  if (!currentUserPermissions.value.canDeleteTasks) return

  try {
    const response = await apiFetch(`${API_URL}/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('Erreur lors de la suppression de la tâche')
    await fetchTasks()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de supprimer la tâche.'
  }
}

// Réinitialise les statistiques (reste en mémoire locale, le backend ne stocke pas cette info)
const resetStats = () => {
  if (!currentUserPermissions.value.canDeleteTasks) return
  if (confirm('⚠️ Êtes-vous sûr de vouloir réinitialiser toutes les statistiques ? Les tâches ne seront pas supprimées, juste marquées comme non effectuées.')) {
    stats.value = {}
  }
}
</script>

<template>
  <header><h1>👨‍👩‍👧‍👦 FamilyTask</h1></header>
  <main>
    <div class="card">
      <!-- Barre d'utilisateur -->
      <div class="user-bar">
        <div class="current-user">
          <Avatar :name="currentMember?.name || ''" :size="28" />
          Connecté: <strong>{{ currentMember?.name }}</strong>
          <span class="role-badge" :class="currentMember?.is_admin ? 'admin' : 'user'">{{ currentMember?.is_admin ? '👑 Admin' : '👶 Utilisateur' }}</span>
        </div>
      </div>

      <div class="todo-header">
        <h2 class="todo-title">📋Tâches à faire</h2>
        <!-- Accès à l'écran Famille, réservé aux admins (création/suppression de comptes, liens de parenté) -->
        <router-link v-if="currentUserPermissions.canManageMembers" to="/famille" class="manage-family-btn">
          👪 Gérer la famille
        </router-link>
      </div>

      <!-- Message d'erreur en cas de problème avec l'API -->
      <div v-if="errorMessage" class="error-message" style="display: block;">
        ⚠️ {{ errorMessage }}
      </div>

      <!-- Statistiques des tâches effectuées -->
      <div class="stats-container">
        <div class="stats-header">
          <div class="stats-title">📊 Tâches effectuées</div>
          <button
            v-if="currentUserPermissions.canDeleteTasks"
            @click="resetStats"
            class="reset-stats-btn"
            title="Réinitialiser toutes les statistiques (Admins seulement)"
          >
            🔄 Réinitialiser
          </button>
        </div>
        <div class="stats-grid">
          <div v-for="member in familyMembers" :key="member.id" class="stat-card" :class="member.is_admin ? 'admin' : 'user'">
            <Avatar :name="member.name" :size="32" />
            <span class="stat-member">{{ member.name }}</span>
            <span class="stat-count">{{ taskStats[member.name] || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- Formulaire pour ajouter une tâche avec autocomplétion - visible seulement pour les admins -->
      <div v-if="currentUserPermissions.canCreateTasks" class="form-container">
        <!-- Overlay transparent pour fermer le dropdown au clic -->
        <div v-if="showSuggestions" class="dropdown-overlay" @click="showSuggestions = false"></div>

        <div class="form-group-wrapper">
          <div class="form-group">
            <!-- Menu "Pour qui ?" visible uniquement pour les admins -->
            <select
              v-if="currentUserPermissions.canManageMembers"
              v-model="selectedMemberId"
              class="assignee-select"
            >
              <option value="">Pour moi</option>
              <option
                v-for="member in familyMembers.filter(m => m.id !== currentMember.id)"
                :key="member.id"
                :value="member.id"
              >
                {{ member.name }}
              </option>
            </select>

            <div class="input-wrapper">
              <input
                v-model="newTask"
                type="text"
                placeholder="Ajouter une nouvelle tâche..."
                @keyup.enter="addTask"
                @focus="showSuggestions = true"
                @blur="window.setTimeout(() => showSuggestions = false, 150)"
              />

              <!-- Dropdown avec les suggestions -->
              <div v-if="showSuggestions && suggestions.length > 0" class="suggestions-dropdown" @click.stop>
                <div
                  v-for="suggestion in suggestions"
                  :key="suggestion"
                  class="suggestion-item"
                  @click="selectSuggestion(suggestion)"
                >
                  💡 {{ suggestion }}
                </div>
              </div>
            </div>
            <button @click="addTask">➕ Ajouter</button>
          </div>
        </div>
      </div>

      <!-- Message pour les utilisateurs sans permission -->
      <div v-else class="no-permission-message">
        ℹ️ Vous ne pouvez que valider les tâches existantes
      </div>

      <!-- Assistant IA : juste en dessous de la barre d'ajout manuel de tâches -->
      <ChatAssistant @refresh-tasks="fetchTasks" />

      <!-- Composant TaskList pour afficher la liste -->
      <TaskList
        :tasks="tasks"
        @toggle="toggleTask"
        @remove="deleteTask"
        :can-delete="currentUserPermissions.canDeleteTasks"
      />
    </div>
  </main>
</template>

<style scoped>
/* Sélection d'utilisateur */
.user-selection {
  text-align: center;
}

.user-selection h2 {
  font-size: 28px;
  color: #7aa86d;
  margin-bottom: 32px;
}

.user-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.user-btn {
  padding: 16px 24px;
  background: linear-gradient(135deg, #7aa86d 0%, #6b8e71 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--btn-shadow);
}

.user-btn:hover {
  transform: translateY(-4px);
  box-shadow: var(--btn-shadow-hover);
}

.user-btn:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

/* Barre d'utilisateur */
.user-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: rgba(122, 168, 109, 0.1);
  border-radius: 10px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
  box-shadow: inset 0 1px 4px rgba(31, 41, 55, 0.06);
}

.current-user {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #2d5a2d;
  font-weight: 600;
}

.role-badge {
  margin-left: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  background: #e8f5e9;
  color: #2d5a2d;
}

.role-badge.admin {
  background: #fff3cd;
  color: #856404;
}

.role-badge.user {
  background: #cfe9f3;
  color: #0c5460;
}

.logout-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #7aa86d 0%, #6b8e71 100%);
  color: white;
  border: none;
  border-radius: 8px;
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

.no-permission-message {
  padding: 16px;
  background: #cfe9f3;
  border-left: 4px solid #0c5460;
  border-radius: 8px;
  margin-bottom: 24px;
  color: #0c5460;
  font-weight: 600;
}

.todo-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.todo-title {
  font-size: 28px;
  font-weight: 800;
  text-align: center;
  margin: 0;
  color: #7aa86d;
  letter-spacing: 0.5px;
}

.manage-family-btn {
  padding: 10px 18px;
  background: linear-gradient(135deg, #7aa86d 0%, #6b8e71 100%);
  color: white;
  border: none;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--btn-shadow);
  text-decoration: none;
  white-space: nowrap;
}

.manage-family-btn:hover {
  transform: translateY(-3px);
  box-shadow: var(--btn-shadow-hover);
}

.manage-family-btn:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

/* Statistiques */
.stats-container {
  background: rgba(122, 168, 109, 0.05);
  border: 2px solid rgba(122, 168, 109, 0.2);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.stats-title {
  font-size: 16px;
  font-weight: 700;
  color: #7aa86d;
  margin: 0;
}

.reset-stats-btn {
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
  white-space: nowrap;
}

.reset-stats-btn:hover {
  transform: translateY(-3px);
  box-shadow: var(--btn-shadow-hover);
}

.reset-stats-btn:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  background: var(--bg-white, #ffffff);
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(31, 41, 55, 0.08);
}

.stat-card:hover {
  border-color: #7aa86d;
  transform: translateY(-3px);
  box-shadow: 0 8px 18px rgba(122, 168, 109, 0.25);
}

.stat-card.admin {
  border-color: #ffc107;
  background: rgba(255, 193, 7, 0.05);
}

.stat-card.user {
  border-color: #2196f3;
  background: rgba(33, 150, 243, 0.05);
}

.stat-member {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 8px;
}

.stat-count {
  display: block;
  font-size: 28px;
  font-weight: 800;
  color: #7aa86d;
}

.form-group-wrapper {
  position: relative;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.assignee-select {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg-white, #ffffff);
  color: var(--text-dark, #1f2937);
  cursor: pointer;
  box-shadow: inset 0 2px 5px rgba(31, 41, 55, 0.08);
}

.assignee-select:focus {
  outline: none;
  border-color: #7aa86d;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.3s ease;
  background: var(--bg-white, #ffffff);
  color: var(--text-dark, #1f2937);
  box-shadow: inset 0 2px 5px rgba(31, 41, 55, 0.08);
}

.form-group input:focus {
  outline: none;
  border-color: #7aa86d;
  box-shadow: inset 0 2px 5px rgba(31, 41, 55, 0.08), 0 0 10px rgba(122, 168, 109, 0.2);
}

.form-group button {
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
  white-space: nowrap;
}

.form-group button:hover {
  transform: translateY(-3px);
  box-shadow: var(--btn-shadow-hover);
}

.form-group button:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

/* Dropdown des suggestions */
.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-white, #ffffff);
  border: 2px solid #7aa86d;
  border-top: none;
  border-radius: 0 0 10px 10px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 6px 15px rgba(122, 168, 109, 0.2);
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: var(--text-dark, #1f2937);
}

.suggestion-item:hover {
  background-color: rgba(122, 168, 109, 0.1);
  padding-left: 20px;
}

.suggestion-item:last-child {
  border-bottom: none;
  border-radius: 0 0 8px 8px;
}

/* Overlay pour fermer le dropdown */
.form-container {
  position: relative;
  margin-bottom: 24px;
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9;
  cursor: pointer;
  pointer-events: auto;
  background: transparent;
}

/* Message d'erreur pour les doublons */
.error-message {
  padding: 12px 16px;
  background: #fee2e2;
  border-left: 4px solid #dc2626;
  border-radius: 8px;
  margin-top: 12px;
  color: #7f1d1d;
  font-weight: 600;
  font-size: 14px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
