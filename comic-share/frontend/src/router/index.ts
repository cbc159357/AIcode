import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/views/AppLayout.vue'),
      redirect: '/workspace',
      children: [
        {
          path: 'workspace',
          name: 'workspace',
          component: () => import('@/components/workspace/WorkspaceView.vue'),
        },
        {
          path: 'tasks',
          name: 'tasks',
          component: () => import('@/views/TaskManager.vue'),
        },
        {
          path: 'workflow',
          component: () => import('@/views/WorkflowView.vue'),
          children: [
            { path: '', redirect: 'library' },
            { path: 'library', name: 'workflow-library', component: () => import('@/components/workflow/WorkflowManager.vue') },
            { path: 'model-check', name: 'workflow-model-check', component: () => import('@/components/workflow/ModelChecker.vue') },
          ],
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/components/settings/SettingsView.vue'),
        },
      ],
    },
  ],
})

export default router
