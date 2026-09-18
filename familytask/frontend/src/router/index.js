import { createRouter, createWebHistory } from 'vue-router'
import Signup from '../views/Signup.vue'
import Login from '../views/Login.vue'
import JoinFamily from '../views/JoinFamily.vue'
import TasksView from '../views/TasksView.vue'
import FamilyView from '../views/FamilyView.vue'
import { fetchCurrentMember } from '../auth.js'

const routes = [
  { path: '/signup', name: 'signup', component: Signup },
  { path: '/login', name: 'login', component: Login },
  { path: '/join', name: 'join', component: JoinFamily },
  // L'assistant IA est intégré directement dans TasksView (composant ChatAssistant), pas de route dédiée
  { path: '/tasks', name: 'tasks', component: TasksView, meta: { requiresAuth: true } },
  // La vérification "admin uniquement" se fait dans FamilyView elle-même (redirection si non-admin),
  // car cette info n'est pas connue du routeur sans appeler l'API /api/me
  { path: '/famille', name: 'famille', component: FamilyView, meta: { requiresAuth: true } },
  { path: '/', redirect: '/tasks' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Garde de navigation : sur une route privée, vérifie la validité réelle du token
// (via /api/me), pas seulement sa présence dans le localStorage
router.beforeEach(async (to, from, next) => {
  if (!to.meta.requiresAuth) {
    next()
    return
  }

  // Pas de token du tout : inutile d'appeler l'API, on redirige directement
  if (!localStorage.getItem('token')) {
    next('/login')
    return
  }

  // Un token est présent : on vérifie qu'il correspond bien à un membre valide.
  // fetchCurrentMember nettoie lui-même le token périmé en cas d'échec (401 ou autre erreur).
  const member = await fetchCurrentMember()
  next(member ? undefined : '/login')
})

export default router