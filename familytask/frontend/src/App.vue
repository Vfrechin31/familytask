<script setup>
import { ref, computed } from 'vue'
import TaskList from './components/TaskList.vue'

// Définition des utilisateurs et leurs rôles
const users = ref([
  { id: 1, name: 'Maman', role: 'admin' },
  { id: 2, name: 'Papa', role: 'admin' },
  { id: 3, name: 'Cloé', role: 'user' },
  { id: 4, name: 'Olivia', role: 'user' }
])

// Définition des permissions par rôle
const rolePermissions = {
  admin: {
    canCreateTasks: true,
    canDeleteTasks: true,
    canManageMembers: true,
    canValidateTasks: true
  },
  user: {
    canCreateTasks: true,
    canDeleteTasks: false,
    canManageMembers: false,
    canValidateTasks: true
  }
}

// Utilisateur actuellement connecté
const currentUser = ref(null)

// Données réactives pour les tâches
const tasks = ref([
  { id: 1, title: 'Faire les courses', done: false, completedBy: null },
])

// Variable pour le nouveau titre de tâche
const newTask = ref('')

// État du dropdown de suggestions
const showSuggestions = ref(false)

// Message d'erreur
const errorMessage = ref('')

// Statistiques persistantes (en mémoire même si tâche supprimée)
const stats = ref({
  'Maman': 0,
  'Papa': 0,
  'Cloé': 0,
  'Olivia': 0
})

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

// Calculer les permissions de l'utilisateur actuel
const currentUserPermissions = computed(() => {
  if (!currentUser.value) {
    return {
      canCreateTasks: false,
      canDeleteTasks: false,
      canManageMembers: false,
      canValidateTasks: false
    }
  }
  return rolePermissions[currentUser.value.role] || {}
})

// Calculer les suggestions filtrées en fonction de ce qui est écrit
const suggestions = computed(() => {
  // Obtenir les titres des tâches existantes (en minuscules pour comparaison)
  const existingTitles = tasks.value.map(t => t.title.toLowerCase())
  
  // Filtrer les tâches communes en excluant celles déjà dans la liste
  let filtered = commonTasks.filter(task => !existingTitles.includes(task.toLowerCase()))
  
  if (newTask.value.trim() === '') {
    // Si le champ est vide, afficher les 8 premières suggestions filtrées
    return filtered.slice(0, 8)
  }
  
  // Sinon, filtrer les suggestions qui commencent par le texte saisi (sans casse)
  const searchTerm = newTask.value.toLowerCase()
  return filtered
    .filter(task => task.toLowerCase().startsWith(searchTerm))
    .slice(0, 8) // Maximum 8 suggestions
})

// Fonction pour ajouter une tâche
const addTask = () => {
  if (!currentUserPermissions.value.canCreateTasks) return
  if (newTask.value.trim() === '') return // Ne pas ajouter si vide
  
  // Créer une nouvelle tâche avec un ID unique
  const newId = Math.max(...tasks.value.map(t => t.id), 0) + 1
  
  tasks.value.push({
    id: newId,
    title: newTask.value,
    done: false,
    completedBy: null
  })
  
  // Vider le champ et fermer le dropdown
  newTask.value = ''
  showSuggestions.value = false
}

// Fonction pour sélectionner une suggestion
const selectSuggestion = (task) => {
  if (!currentUserPermissions.value.canCreateTasks) return
  newTask.value = task
  showSuggestions.value = false
  // Ajouter automatiquement la tâche
  addTask()
}

// Fonction pour changer l'état "done" d'une tâche
const toggleTask = (id) => {
  if (!currentUserPermissions.value.canValidateTasks) return
  const task = tasks.value.find(t => t.id === id)
  if (task) {
    task.done = !task.done
    // Enregistrer qui a effectué la tâche et incrémenter les stats
    if (task.done) {
      task.completedBy = currentUser.value.name
      stats.value[currentUser.value.name]++
    } else {
      task.completedBy = null
      stats.value[currentUser.value.name]--
    }
  }
}

// Calculer les statistiques de tâches effectuées par personne
const taskStats = computed(() => {
  return stats.value
})

// Fonction pour supprimer une tâche
const deleteTask = (id) => {
  if (!currentUserPermissions.value.canDeleteTasks) return
  tasks.value = tasks.value.filter(t => t.id !== id)
}

// Fonction pour réinitialiser les statistiques
const resetStats = () => {
  if (!currentUserPermissions.value.canDeleteTasks) return
  if (confirm('⚠️ Êtes-vous sûr de vouloir réinitialiser toutes les statistiques ? Les tâches ne seront pas supprimées, juste marquées comme non effectuées.')) {
    tasks.value.forEach(task => {
      task.done = false
      task.completedBy = null
    })
    // Réinitialiser les compteurs
    stats.value['Maman'] = 0
    stats.value['Papa'] = 0
    stats.value['Cloé'] = 0
    stats.value['Olivia'] = 0
  }
}

// Fonction pour changer d'utilisateur
const switchUser = (user) => {
  currentUser.value = user
  newTask.value = ''
  showSuggestions.value = false
}
</script>

<template>
  <header><h1>👨‍👩‍👧‍👦 FamilyTask</h1></header>
  <main>
    <!-- Sélection d'utilisateur si personne n'est connecté -->
    <div v-if="!currentUser" class="card user-selection">
      <h2>👤 Qui es-tu ?</h2>
      <div class="user-buttons">
        <button 
          v-for="user in users" 
          :key="user.id"
          @click="switchUser(user)"
          class="user-btn"
        >
          {{ user.name }}
        </button>
      </div>
    </div>

    <!-- Contenu principal si utilisateur connecté -->
    <div v-else class="card">
      <!-- Barre d'utilisateur -->
      <div class="user-bar">
        <div class="current-user">
          👤 Connecté: <strong>{{ currentUser.name }}</strong>
          <span class="role-badge" :class="currentUser.role">{{ currentUser.role === 'admin' ? '👑 Admin' : '👶 Utilisateur' }}</span>
        </div>
        <button @click="currentUser = null" class="logout-btn">Changer d'utilisateur</button>
      </div>

      <h2 class="todo-title">📋Tâches à faire</h2>
      
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
          <div v-for="user in users" :key="user.id" class="stat-card" :class="user.role">
            <span class="stat-member">{{ user.name }}</span>
            <span class="stat-count">{{ taskStats[user.name] || 0 }}</span>
          </div>
        </div>
      </div>
      
      <!-- Formulaire pour ajouter une tâche avec autocomplétion - visible seulement pour les admins -->
      <div v-if="currentUserPermissions.canCreateTasks" class="form-container">
        <!-- Overlay transparent pour fermer le dropdown au clic -->
        <div v-if="showSuggestions" class="dropdown-overlay" @click="showSuggestions = false"></div>
        
        <div class="form-group-wrapper">
          <div class="form-group">
            <div class="input-wrapper">
              <input 
                v-model="newTask" 
                type="text" 
                placeholder="Ajouter une nouvelle tâche..."
                @keyup.enter="addTask"
                @focus="showSuggestions = true"
                @blur="setTimeout(() => showSuggestions = false, 150)"
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
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(122, 168, 109, 0.3);
}

.user-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(122, 168, 109, 0.4);
}

.user-btn:active {
  transform: translateY(-2px);
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
}

.current-user {
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
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(122, 168, 109, 0.3);
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(122, 168, 109, 0.4);
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

.todo-title {
  font-size: 28px;
  font-weight: 800;
  text-align: center;
  margin: 0 0 24px;
  color: #7aa86d;
  letter-spacing: 0.5px;
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
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(122, 168, 109, 0.3);
  white-space: nowrap;
}

.reset-stats-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(122, 168, 109, 0.4);
}

.reset-stats-btn:active {
  transform: translateY(0);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.stat-card {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-color: #7aa86d;
  box-shadow: 0 2px 8px rgba(122, 168, 109, 0.15);
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
}

.form-group input:focus {
  outline: none;
  border-color: #7aa86d;
  box-shadow: 0 0 10px rgba(122, 168, 109, 0.2);
}

.form-group button {
  padding: 12px 20px;
  background: linear-gradient(135deg, #7aa86d 0%, #6b8e71 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(122, 168, 109, 0.3);
  white-space: nowrap;
}

.form-group button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(122, 168, 109, 0.4);
}

.form-group button:active {
  transform: translateY(0);
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
  display: none; /* Désactivé */
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
