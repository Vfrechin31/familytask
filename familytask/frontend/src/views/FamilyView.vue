<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiFetch from '../api.js'
import Avatar from '../components/Avatar.vue'

const router = useRouter()

// Membre actuellement connecté (permet de savoir qui est "soi-même" dans la liste)
const currentMember = ref(null)

// Listes chargées depuis l'API
const members = ref([])
const liens = ref([])
const familyTasks = ref([])

// Message d'erreur générique affiché en haut de la page
const errorMessage = ref('')

// Champs du formulaire d'ajout d'un membre
const newMemberName = ref('')
const newMemberLien = ref('')
const newMemberEmail = ref('')
const newMemberPassword = ref('')
const newMemberIsAdmin = ref(false)

// Champ du petit formulaire d'ajout d'un lien de parenté
const newLienNom = ref('')

// Texte affiché sur le bouton de copie du code famille ("Copier" -> "Copié !" temporairement)
const copyLabel = ref('Copier le lien')

// Lien d'invitation complet, à partager par n'importe quel canal (SMS, WhatsApp...) :
// ouvre directement le formulaire /join avec le code pré-rempli
const inviteLink = () => `${window.location.origin}/join?code=${currentMember.value?.family_code}`

// Copie le lien d'invitation dans le presse-papiers, avec un petit retour visuel
const copyInviteLink = async () => {
  try {
    await navigator.clipboard.writeText(inviteLink())
    copyLabel.value = 'Copié !'
    setTimeout(() => { copyLabel.value = 'Copier le lien' }, 2000)
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de copier le lien, copie-le manuellement.'
  }
}

// Récupère la liste des membres de la famille (moi compris)
const fetchMembers = async () => {
  try {
    const response = await apiFetch('/members')
    if (!response.ok) throw new Error('Erreur lors du chargement des membres')
    members.value = await response.json()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de charger les membres de la famille.'
  }
}

// Récupère la liste des liens de parenté propres à la famille
const fetchLiens = async () => {
  try {
    const response = await apiFetch('/liens')
    if (!response.ok) throw new Error('Erreur lors du chargement des liens')
    liens.value = await response.json()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de charger les liens de parenté.'
  }
}

// Récupère toutes les tâches de la famille (réservé aux admins côté API)
const fetchFamilyTasks = async () => {
  try {
    const response = await apiFetch('/tasks/famille')
    if (!response.ok) throw new Error('Erreur lors du chargement des tâches')
    familyTasks.value = await response.json()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de charger les tâches de la famille.'
  }
}

// Retrouve le prénom d'un membre à partir de son id, pour l'affichage des tâches
const getMemberName = (memberId) => {
  const member = members.value.find(m => m.id === memberId)
  return member ? member.name : '?'
}

// Ajoute un nouveau membre à la famille (réservé aux admins côté API)
const addMember = async () => {
  errorMessage.value = ''

  try {
    const response = await apiFetch('/members', {
      method: 'POST',
      body: JSON.stringify({
        name: newMemberName.value,
        lien: newMemberLien.value,
        email: newMemberEmail.value,
        password: newMemberPassword.value,
        is_admin: newMemberIsAdmin.value
      })
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || "Erreur lors de la création du membre")
    }

    // On réinitialise le formulaire et on recharge la liste à jour
    newMemberName.value = ''
    newMemberLien.value = ''
    newMemberEmail.value = ''
    newMemberPassword.value = ''
    newMemberIsAdmin.value = false
    await fetchMembers()
  } catch (error) {
    errorMessage.value = error.message
  }
}

// Supprime un membre (sauf soi-même) après confirmation
const deleteMember = async (member) => {
  if (member.id === currentMember.value?.id) return // Sécurité côté client, le serveur refuse aussi

  if (!confirm(`⚠️ Supprimer ${member.name} et toutes ses tâches ? Cette action est irréversible.`)) {
    return
  }

  try {
    const response = await apiFetch(`/members/${member.id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('Erreur lors de la suppression du membre')

    await fetchMembers()
    await fetchFamilyTasks() // Les tâches du membre supprimé disparaissent aussi
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de supprimer ce membre.'
  }
}

// Ajoute un nouveau lien de parenté à la liste de la famille
const addLien = async () => {
  if (newLienNom.value.trim() === '') return

  try {
    const response = await apiFetch('/liens', {
      method: 'POST',
      body: JSON.stringify({ nom: newLienNom.value })
    })
    if (!response.ok) throw new Error("Erreur lors de l'ajout du lien")

    newLienNom.value = ''
    await fetchLiens()
  } catch (error) {
    console.error(error)
    errorMessage.value = "Impossible d'ajouter ce lien de parenté."
  }
}

// Supprime une tâche de n'importe quel membre de la famille (réservé aux admins côté API) :
// permet à un admin de corriger une erreur d'attribution/création de tâche
const deleteFamilyTask = async (task) => {
  if (!confirm(`Supprimer la tâche "${task.title}" ?`)) return

  try {
    const response = await apiFetch(`/tasks/${task.id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('Erreur lors de la suppression de la tâche')
    await fetchFamilyTasks()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de supprimer cette tâche.'
  }
}

// Supprime un lien de parenté qui n'est plus nécessaire
const deleteLien = async (lien) => {
  if (!confirm(`Supprimer le lien "${lien.nom}" ?`)) return

  try {
    const response = await apiFetch(`/liens/${lien.id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('Erreur lors de la suppression du lien')
    await fetchLiens()
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Impossible de supprimer ce lien de parenté.'
  }
}

// Au chargement : on vérifie d'abord que je suis bien admin avant de charger quoi que ce soit d'autre
onMounted(async () => {
  try {
    const response = await apiFetch('/me')
    if (!response.ok) throw new Error('Token invalide')

    const data = await response.json()
    if (!data.is_admin) {
      router.push('/tasks') // Cette page est réservée aux administrateurs
      return
    }

    currentMember.value = data
    await Promise.all([fetchMembers(), fetchLiens(), fetchFamilyTasks()])
  } catch (error) {
    console.error(error)
    router.push('/tasks')
  }
})
</script>

<template>
  <header>
    <router-link to="/tasks" class="back-btn" title="Retour aux tâches">← Tâches</router-link>
    <h1>👪 Ma famille</h1>
  </header>
  <main>
    <div v-if="errorMessage" class="card error-message">⚠️ {{ errorMessage }}</div>

    <!-- Code d'invitation : à partager pour que quelqu'un rejoigne la famille lui-même,
         sans que l'admin ait à créer son compte à sa place -->
    <div class="card">
      <h2>🔗 Inviter un membre</h2>
      <p class="hint">Partage ce code ou ce lien : la personne pourra créer elle-même son compte et choisir son mot de passe.</p>
      <div class="invite-row">
        <span class="invite-code">{{ currentMember?.family_code }}</span>
        <button class="invite-copy-btn" @click="copyInviteLink">{{ copyLabel }}</button>
      </div>
    </div>

    <!-- Liste des membres -->
    <div class="card">
      <h2>👤 Membres</h2>
      <ul class="member-list">
        <li v-for="member in members" :key="member.id" class="member-item">
          <div class="member-info">
            <Avatar :name="member.name" :size="36" />
            <span class="member-name">{{ member.name }}</span>
            <span class="member-lien">{{ member.lien }}</span>
            <span v-if="member.is_admin" class="admin-badge">👑 Admin</span>
          </div>
          <!-- Ni soi-même, ni un autre administrateur, ne peuvent être supprimés (cohérent avec le contrôle côté backend) -->
          <button
            v-if="member.id !== currentMember?.id && !member.is_admin"
            class="delete-btn"
            title="Supprimer ce membre"
            @click="deleteMember(member)"
          >
            ✕
          </button>
        </li>
      </ul>
    </div>

    <!-- Formulaire d'ajout d'un membre -->
    <div class="card">
      <h2>➕ Ajouter un membre</h2>
      <form @submit.prevent="addMember" class="member-form">
        <input v-model="newMemberName" type="text" placeholder="Prénom" required />

        <select v-model="newMemberLien" required>
          <option value="" disabled>Lien de parenté</option>
          <option v-for="lien in liens" :key="lien.id" :value="lien.nom">{{ lien.nom }}</option>
        </select>

        <input v-model="newMemberEmail" type="email" placeholder="Email" required />
        <input v-model="newMemberPassword" type="password" placeholder="Mot de passe" required />

        <label class="admin-checkbox">
          <input v-model="newMemberIsAdmin" type="checkbox" />
          Administrateur
        </label>

        <button type="submit">Créer le compte</button>
      </form>
    </div>

    <!-- Liens de parenté -->
    <div class="card">
      <h2>🔗 Liens de parenté</h2>
      <div class="lien-tags">
        <span v-for="lien in liens" :key="lien.id" class="lien-tag">
          {{ lien.nom }}
          <button class="lien-delete-btn" title="Supprimer ce lien" @click="deleteLien(lien)">✕</button>
        </span>
        <span v-if="liens.length === 0" class="hint">Aucun lien pour le moment.</span>
      </div>
      <div class="lien-form">
        <input
          v-model="newLienNom"
          type="text"
          placeholder="Nouveau lien (ex. Tonton, Cousine...)"
          @keyup.enter="addLien"
        />
        <button @click="addLien">Ajouter</button>
      </div>
    </div>

    <!-- Toutes les tâches de la famille -->
    <div class="card">
      <h2>📋 Tâches de la famille</h2>
      <ul class="family-task-list">
        <li v-for="task in familyTasks" :key="task.id" class="family-task-item">
          <div class="family-task-info">
            <span :class="{ done: task.done }">{{ task.title }}</span>
            <span class="family-task-assignee">{{ getMemberName(task.member_id) }}</span>
          </div>
          <button
            class="delete-btn"
            title="Supprimer cette tâche"
            @click="deleteFamilyTask(task)"
          >
            ✕
          </button>
        </li>
      </ul>
      <p v-if="familyTasks.length === 0" class="empty-message">Aucune tâche pour le moment.</p>
    </div>
  </main>
</template>

<style scoped>
header {
  position: relative;
}

.back-btn {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.3);
  color: #1f2937;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  box-shadow: none;
  transition: background 0.2s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.5);
}

.invite-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.invite-code {
  padding: 10px 16px;
  border-radius: 12px;
  background: rgba(122, 168, 109, 0.15);
  color: #2d5a2d;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
}

.invite-copy-btn {
  padding: 10px 16px;
  background: linear-gradient(135deg, #7aa86d 0%, #6b8e71 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--btn-shadow);
  transition: all 0.2s ease;
}

.invite-copy-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--btn-shadow-hover);
}

.invite-copy-btn:active {
  transform: translateY(1px);
  box-shadow: var(--btn-shadow-active);
}

.member-list,
.family-task-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: var(--bg-light, #f8f7f5);
  border-radius: 12px;
  margin-bottom: 8px;
  box-shadow: 0 4px 10px rgba(31, 41, 55, 0.08);
}

.member-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.member-name {
  font-weight: 700;
  color: var(--text-dark, #1f2937);
}

.member-lien {
  font-size: 12px;
  color: var(--text-muted, #6b7280);
}

.admin-badge {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  background: #fff3cd;
  color: #856404;
}

.delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--bg-white, #ffffff);
  color: #ef4444;
  border: none;
  border-radius: 50%;
  padding: 0;
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(239, 68, 68, 0.3), 0 2px 4px rgba(0, 0, 0, 0.12);
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background: #fee2e2;
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(239, 68, 68, 0.4), 0 4px 8px rgba(0, 0, 0, 0.15);
}

.delete-btn:active {
  transform: translateY(1px);
  box-shadow: inset 0 3px 6px rgba(239, 68, 68, 0.3);
}

.member-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-form select {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg-white, #ffffff);
  color: var(--text-dark, #1f2937);
}

.admin-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-dark, #1f2937);
  cursor: pointer;
}

.lien-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.lien-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px 6px 14px;
  border-radius: 20px;
  background: rgba(122, 168, 109, 0.15);
  color: #2d5a2d;
  font-size: 13px;
  font-weight: 600;
}

.lien-delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  padding: 0;
  background: rgba(45, 90, 45, 0.15);
  color: #2d5a2d;
  border: none;
  border-radius: 50%;
  font-size: 10px;
  line-height: 1;
  cursor: pointer;
  box-shadow: none;
  transition: all 0.2s ease;
}

.lien-delete-btn:hover {
  background: #ef4444;
  color: white;
  transform: translateY(0) scale(1.1);
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4);
}

.lien-form {
  display: flex;
  gap: 10px;
}

.family-task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: var(--bg-light, #f8f7f5);
  border-radius: 12px;
  margin-bottom: 8px;
  box-shadow: 0 4px 10px rgba(31, 41, 55, 0.08);
}

.family-task-item span.done {
  text-decoration: line-through;
  color: var(--text-muted, #6b7280);
}

.family-task-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.family-task-assignee {
  font-size: 12px;
  font-weight: 700;
  color: #7aa86d;
}

.error-message {
  background: #fee2e2;
  border-left: 4px solid #dc2626;
  color: #7f1d1d;
  font-weight: 600;
}
</style>
