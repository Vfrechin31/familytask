<script setup>
// Props : recevoir la liste des tâches du parent (App.vue)
const props = defineProps({
  tasks: {
    type: Array,
    required: true
  },
  canDelete: {
    type: Boolean,
    default: false
  }
})

// Événements : définir ce que ce composant peut émettre
const emit = defineEmits(['toggle', 'remove'])

// Messages sympa aléatoires quand la liste est vide
const emptyMessages = [
  'Tu es libre, va profiter de la vie !',
  "Tu a été super efficace, tu as le droit à un gâteau !",
  "Il est temps d'aller t'amuser !"
]

// Fonction pour obtenir un message aléatoire
const getRandomMessage = () => {
  return emptyMessages[Math.floor(Math.random() * emptyMessages.length)]
}

// Fonctions pour émettre les événements vers le parent
const handleToggle = (id) => {
  emit('toggle', id)
}

const handleRemove = (id) => {
  emit('remove', id)
}
</script>

<template>
  <!-- Affichage de la liste des tâches -->
  <ul class="task-list">
    <li v-for="task in tasks" :key="task.id" class="task-item">
      <!-- Case à cocher -->
      <input 
        type="checkbox" 
        :checked="task.done"
        @change="handleToggle(task.id)"
      />
      <!-- Titre de la tâche (barré si done = true) -->
      <span :class="{ done: task.done }">{{ task.title }}</span>
      <!-- Bouton de suppression - visible pour tous mais désactivé pour les users -->
      <button 
        class="delete-btn" 
        :class="{ disabled: !props.canDelete }"
        @click="props.canDelete && handleRemove(task.id)"
        :title="props.canDelete ? 'Supprimer la tâche' : 'Vous n\'avez pas la permission de supprimer'"
      >
        🗑️
      </button>
    </li>
  </ul>

  <!-- Message si la liste est vide -->
  <p v-if="tasks.length === 0" class="empty-message">✨ {{ getRandomMessage() }}</p>
</template>

<style scoped>
.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background-color: var(--bg-white, #ffffff);
  border-radius: 12px;
  margin-bottom: 10px;
  transition: all 0.3s ease;
  border: 1px solid rgba(139, 92, 246, 0.1);
  box-shadow: 0 4px 12px rgba(31, 41, 55, 0.08);
}

.task-item:hover {
  background-color: var(--bg-light, #f8f7ff);
  border-color: rgba(139, 92, 246, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(139, 92, 246, 0.18);
}

.task-item span {
  flex: 1;
  font-size: 15px;
  color: var(--text-dark, #1f2937);
  transition: all 0.3s ease;
}

.task-item span.done {
  text-decoration: line-through;
  color: var(--text-muted, #6b7280);
  font-weight: 500;
}

/* Bouton supprimer */
.delete-btn {
  background-color: transparent;
  color: #ef4444;
  border: none;
  padding: 6px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s ease;
  box-shadow: none !important;
  transform: none !important;
}

.delete-btn:hover:not(:disabled) {
  background-color: rgba(239, 68, 68, 0.1);
  transform: scale(1.1);
}

.delete-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.delete-btn:disabled,
.delete-btn.disabled {
  color: #d1d5db;
  cursor: not-allowed;
  opacity: 0.5;
}

.delete-btn:disabled:hover,
.delete-btn.disabled:hover {
  background-color: transparent;
  transform: none;
}

/* Message vide */
.empty-message {
  text-align: center;
  color: #7aa86d;
  margin-top: 32px;
  font-size: 18px;
  padding: 28px;
  font-weight: 600;
  font-family: 'Georgia', 'Palatino', serif;
  font-style: italic;
  letter-spacing: 0.3px;
}
</style>
