<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const role = computed(() => String(route.params.role || route.meta.registerRole || 'student'))
const registering = computed(() => route.path.startsWith('/register'))
const roles = [
  { id: 'student', label: '学生', noun: '姓名' },
  { id: 'teacher', label: '教师', noun: '姓名' },
  { id: 'admin', label: '管理员', noun: '用户名' },
]
const roleInfo = computed(() => roles.find(item => item.id === role.value) || roles[0])
const form = reactive({ name: '', username: '', password: '', major: '', grade: '', title: '', department: '' })
const busy = ref(false)
const error = ref('')

async function submit() {
  busy.value = true
  error.value = ''
  try {
    if (registering.value) {
      await api('/api/auth/register', { method: 'POST', body: JSON.stringify({ role: role.value, ...form }) })
      await router.push(`/login/${role.value}`)
      return
    }
    const result = await api<{ redirect: string }>('/api/auth/login', {
      method: 'POST', body: JSON.stringify({ role: role.value, ...form }),
    })
    await router.push(result.redirect)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '操作失败，请稍后重试'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <div class="brand-mark">C</div>
      <p class="eyebrow">COURSE COMPASS</p>
      <h1>{{ registering ? `创建${roleInfo.label}账号` : `${roleInfo.label}登录` }}</h1>
      <p class="muted auth-subtitle">发现适合你的下一门课</p>
      <form class="form-stack" @submit.prevent="submit">
        <label>{{ roleInfo.noun }}
          <input v-if="role === 'admin'" v-model="form.username" required autocomplete="username" />
          <input v-else v-model="form.name" required autocomplete="name" />
        </label>
        <template v-if="registering && role === 'student'">
          <label>专业<input v-model="form.major" placeholder="例如：计算机科学与技术" /></label>
          <label>年级<input v-model="form.grade" placeholder="例如：2025级" /></label>
        </template>
        <template v-if="registering && role === 'teacher'">
          <label>职称<input v-model="form.title" placeholder="例如：讲师" /></label>
          <label>院系<input v-model="form.department" placeholder="例如：计算机学院" /></label>
        </template>
        <label>密码<input v-model="form.password" required type="password" autocomplete="current-password" /></label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="button button--primary button--wide" :disabled="busy">
          {{ busy ? '请稍候…' : registering ? '创建账号' : '登录' }}
        </button>
      </form>
      <div class="auth-links">
        <template v-if="registering">
          <RouterLink :to="`/login/${role}`">已有账号？返回登录</RouterLink>
        </template>
        <template v-else>
          <RouterLink v-if="role !== 'admin'" :to="role === 'student' ? '/register' : '/register/teacher'">注册{{ roleInfo.label }}账号</RouterLink>
          <RouterLink v-if="role !== 'student'" to="/login/student">学生入口</RouterLink>
          <RouterLink v-if="role !== 'teacher'" to="/login/teacher">教师入口</RouterLink>
          <RouterLink v-if="role !== 'admin'" to="/login/admin">管理员入口</RouterLink>
        </template>
      </div>
    </section>
  </main>
</template>
