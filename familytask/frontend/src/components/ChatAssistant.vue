<script setup>
import { ref, nextTick, onBeforeUnmount } from 'vue'
import apiFetch from '../api.js'

// Émis après chaque réponse de l'assistant, pour que le parent (TasksView) rafraîchisse sa liste.
// On ne sait pas toujours, côté front, si une tâche a réellement été créée par l'assistant,
// donc on émet systématiquement après une réponse réussie : c'est sans risque.
const emit = defineEmits(['refresh-tasks'])

// Historique de la conversation affiché dans la zone de messages
const messages = ref([])

// Contenu du champ de saisie
const newMessage = ref('')

// Empêche l'envoi en double pendant qu'une réponse est en attente
const isSending = ref(false)

// Message d'erreur réseau/API, affiché au-dessus du champ de saisie
const errorMessage = ref('')

// Référence vers la zone de messages, pour faire défiler automatiquement vers le bas
const messagesZone = ref(null)

// Fait défiler la zone de messages tout en bas, une fois le DOM mis à jour
const scrollToBottom = async () => {
  await nextTick()
  if (messagesZone.value) {
    messagesZone.value.scrollTop = messagesZone.value.scrollHeight
  }
}

// Envoie le message courant à l'assistant IA et affiche sa réponse
const sendMessage = async () => {
  const texte = newMessage.value.trim()
  if (texte === '' || isSending.value) return

  messages.value.push({ role: 'user', text: texte })
  newMessage.value = ''
  errorMessage.value = ''
  isSending.value = true
  scrollToBottom()

  try {
    const response = await apiFetch('/assistant', {
      method: 'POST',
      body: JSON.stringify({ message: texte })
    })

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || "L'assistant n'a pas pu répondre.")
    }

    const data = await response.json()
    messages.value.push({ role: 'assistant', text: data.reply })
    emit('refresh-tasks')
  } catch (error) {
    console.error(error)
    errorMessage.value = error.message || "Impossible de contacter l'assistant."
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

// --- Dictée vocale (API SpeechRecognition du navigateur) ---

// Chrome/Edge exposent l'API sous le nom préfixé "webkitSpeechRecognition"
const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition
const speechSupported = !!SpeechRecognitionApi

const isListening = ref(false)
let recognition = null

if (speechSupported) {
  recognition = new SpeechRecognitionApi()
  recognition.lang = 'fr-FR'
  recognition.interimResults = false
  recognition.maxAlternatives = 1

  recognition.onresult = (event) => {
    newMessage.value = event.results[0][0].transcript
  }

  recognition.onend = () => {
    isListening.value = false
  }

  recognition.onerror = () => {
    isListening.value = false
  }
}

// Démarre la dictée vocale (pas d'action si déjà en cours ou non supportée par le navigateur)
const startListening = () => {
  if (!speechSupported || isListening.value) return
  isListening.value = true
  recognition.start()
}

// On arrête proprement la reconnaissance vocale si le composant est démonté en pleine écoute
onBeforeUnmount(() => {
  if (recognition && isListening.value) {
    recognition.stop()
  }
})
</script>

<template>
  <div class="assistant-container">
    <div class="assistant-header">
      <span class="assistant-title">🤖 Demander à l'assistant</span>
    </div>

    <div v-if="errorMessage" class="error-message">⚠️ {{ errorMessage }}</div>

    <!-- Zone de messages : masquée tant qu'il n'y a rien à afficher, pour rester compacte -->
    <div v-if="messages.length > 0 || isSending" ref="messagesZone" class="messages-zone">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="message"
        :class="message.role === 'user' ? 'message-user' : 'message-assistant'"
      >
        {{ message.text }}
      </div>

      <div v-if="isSending" class="message message-assistant message-pending">
        🤖 L'assistant réfléchit…
      </div>
    </div>

    <p v-else class="hint">Ex. « Ajoute une tâche vaisselle pour Cloé »</p>

    <!-- Champ de saisie + micro + bouton d'envoi -->
    <div class="form-group">
      <button
        type="button"
        class="mic-btn"
        :class="{ listening: isListening }"
        :disabled="!speechSupported"
        :title="speechSupported ? 'Dicter la phrase' : 'Reconnaissance vocale non supportée par ce navigateur'"
        @click="startListening"
      >
        {{ isListening ? '🔴' : '🎤' }}
      </button>

      <input
        v-model="newMessage"
        type="text"
        placeholder="Écris ta demande..."
        :disabled="isSending"
        @keyup.enter="sendMessage"
      />

      <button type="button" @click="sendMessage" :disabled="isSending">
        Envoyer
      </button>
    </div>
  </div>
</template>

<style scoped>
.assistant-container {
  background: rgba(122, 168, 109, 0.05);
  border: 2px solid rgba(122, 168, 109, 0.2);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.assistant-header {
  margin-bottom: 10px;
}

.assistant-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
}

.hint {
  margin: 0 0 12px;
}

.messages-zone {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  padding: 2px 2px 4px;
  margin-bottom: 12px;
}

.message {
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.4;
  white-space: pre-wrap;
  box-shadow: 0 4px 10px rgba(31, 41, 55, 0.08);
}

.message-user {
  align-self: flex-end;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-assistant {
  align-self: flex-start;
  background: var(--bg-white, #ffffff);
  color: var(--text-dark);
  border-bottom-left-radius: 4px;
}

.message-pending {
  font-style: italic;
  color: var(--text-muted);
}

.mic-btn {
  flex: 0 0 auto;
  padding: 10px 14px;
  font-size: 16px;
}

.mic-btn.listening {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  box-shadow: 0 0 0 4px rgba(220, 38, 38, 0.2);
}

.mic-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  box-shadow: none;
}

.error-message {
  padding: 10px 14px;
  background: #fee2e2;
  border-left: 4px solid #dc2626;
  border-radius: 8px;
  margin-bottom: 12px;
  color: #7f1d1d;
  font-weight: 600;
  font-size: 13px;
}
</style>
